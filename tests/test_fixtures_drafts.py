# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Tests for the model record fixtures running against the real draft service of the mock model."""

from __future__ import annotations

import gzip
import hashlib
import logging
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from types import SimpleNamespace

import pytest
from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_rdm_records.fixtures import FixturesEngine
from mock_module.api import PIDProvider

from oarepo_runtime import fixtures
from oarepo_runtime.fixtures import loader


@pytest.fixture
def mock_fixtures(app, db, search_with_field_mapping, search_clear, location, tmp_path):
    """Return a loader writing ``yaml`` as the mock model's fixture file and loading it."""

    def load(yaml: str) -> None:
        (tmp_path / "mock.yaml").write_text(yaml)
        fixtures.ModelRecordFixtures("mock", tmp_path).load()

    return load


def _read(service, id_: str) -> dict:
    return service.read(system_identity, id_).to_dict()


def _files(file_service, id_: str) -> dict[str, dict]:
    return {f["key"]: f for f in file_service.list_files(system_identity, id_).to_dict()["entries"]}


def test_creates_and_publishes_record_with_entry_id(mock_fixtures, service):
    """An entry's ``id`` becomes the pid of the published record."""
    mock_fixtures("- id: abcde-12345\n  metadata:\n    title: Created\n  files:\n    enabled: false\n")

    assert _read(service, "abcde-12345")["metadata"] == {"title": "Created"}
    assert service.draft_cls.pid.field._provider is PIDProvider


def test_updates_published_record_through_new_draft(mock_fixtures, service):
    """A published record with the entry's ``id`` is edited, updated and published again."""
    mock_fixtures("- id: upd-1\n  metadata:\n    title: Original\n  files:\n    enabled: false\n")
    mock_fixtures("- id: upd-1\n  metadata:\n    title: Updated\n  files:\n    enabled: false\n")

    assert _read(service, "upd-1")["metadata"] == {"title": "Updated"}


def test_updates_existing_draft_and_publishes_it(mock_fixtures, service):
    """An unpublished draft with the entry's ``id`` is updated and published."""
    mock_fixtures("- id: drf-1\n  metadata:\n    title: Original\n  files:\n    enabled: false\n")
    service.edit(system_identity, "drf-1")

    mock_fixtures("- id: drf-1\n  metadata:\n    title: Updated\n  files:\n    enabled: false\n")

    assert _read(service, "drf-1")["metadata"] == {"title": "Updated"}
    with pytest.raises(PIDDoesNotExistError):
        service.read_draft(system_identity, "drf-1")


def _md5(content: bytes) -> str:
    return f"md5:{hashlib.md5(content).hexdigest()}"  # noqa: S324


def _files_fixture(tmp_path, files: dict[str, bytes]) -> str:
    """Write ``files`` into ``app_data/files`` and return a fixture listing them with size and checksum."""
    (tmp_path / "files").mkdir(exist_ok=True)
    entries = ""
    for key, content in files.items():
        (tmp_path / "files" / key).write_bytes(content)
        entries += (
            f"      - key: {key}\n"
            f"        path: files/{key}\n"
            f"        size: {len(content)}\n"
            f"        checksum: {_md5(content)}\n"
        )
    return "- id: fil-1\n  metadata:\n    title: With files\n  files:\n    entries:\n" + entries


def test_uploads_local_files(mock_fixtures, service, tmp_path):
    """A local file is uploaded from ``app_data`` and the record is published with it."""
    mock_fixtures(_files_fixture(tmp_path, {"1.txt": b"hello"}))

    record_files = _files(service.files, "fil-1")
    assert set(record_files) == {"1.txt"}
    assert record_files["1.txt"]["size"] == 5
    assert record_files["1.txt"]["checksum"] == _md5(b"hello")


@pytest.mark.parametrize(("content", "reuploaded"), [(b"hello", False), (b"changed", True)])
def test_reuploads_only_changed_files(mock_fixtures, service, tmp_path, content, reuploaded):
    """Re-loading keeps a file whose content is unchanged and replaces a changed one."""
    mock_fixtures(_files_fixture(tmp_path, {"1.txt": b"hello"}))
    file_id = _files(service.files, "fil-1")["1.txt"]["file_id"]

    mock_fixtures(_files_fixture(tmp_path, {"1.txt": content}))

    record_file = _files(service.files, "fil-1")["1.txt"]
    assert (record_file["size"], record_file["checksum"]) == (len(content), _md5(content))
    assert (record_file["file_id"] != file_id) == reuploaded


def test_deletes_files_missing_from_fixture(mock_fixtures, service, tmp_path):
    """A file of a published record that the fixture no longer lists is deleted."""
    mock_fixtures(_files_fixture(tmp_path, {"1.txt": b"hello", "2.txt": b"other"}))

    mock_fixtures(_files_fixture(tmp_path, {"1.txt": b"hello"}))

    assert set(_files(service.files, "fil-1")) == {"1.txt"}


@pytest.fixture
def http_server():
    """Serve ``b"fetched"`` on a local HTTP server, gzip-compressed when the request path ends with ``.gz``."""

    class Handler(BaseHTTPRequestHandler):
        def do_GET(self):
            body = gzip.compress(b"fetched") if self.path.endswith(".gz") else b"fetched"
            self.send_response(200)
            if self.path.endswith(".gz"):
                self.send_header("Content-Encoding", "gzip")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, *args):
            pass

    server = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{server.server_port}"
    server.shutdown()
    thread.join()


@pytest.mark.parametrize(("id_", "path"), [("fet-1", "/f.txt"), ("fet-2", "/f.txt.gz")], ids=["plain", "gzip-encoded"])
def test_downloads_fetch_files_before_publishing(mock_fixtures, service, http_server, id_, path):
    """A fetch file is downloaded (and transport-decoded) by the fixture, so the record is published right away."""
    mock_fixtures(
        f"- id: {id_}\n"
        "  metadata:\n"
        "    title: Fetched\n"
        "  files:\n"
        "    entries:\n"
        "      - key: f.txt\n"
        "        size: 7\n"
        f"        checksum: {_md5(b'fetched')}\n"
        "        transfer:\n"
        "          type: F\n"
        f"          url: {http_server}{path}\n"
    )

    record_file = _files(service.files, id_)["f.txt"]
    assert (record_file["size"], record_file["checksum"]) == (7, _md5(b"fetched"))
    assert record_file["transfer"]["type"] == "L"
    with service.files.get_file_content(system_identity, id_, "f.txt").get_stream("rb") as stream:
        assert stream.read() == b"fetched"


def test_logs_failed_entry_and_continues(mock_fixtures, service, caplog):
    """An invalid entry is logged as an error and the following entries are still loaded."""
    with caplog.at_level(logging.ERROR, logger="oarepo_runtime.fixtures"):
        mock_fixtures(
            "- id: bad-1\n  metadata:\n    title: x\n  files:\n    enabled: false\n"
            "- id: good-1\n  metadata:\n    title: Good\n  files:\n    enabled: false\n"
        )

    assert _read(service, "good-1")["metadata"] == {"title": "Good"}
    [record] = caplog.records
    assert record.getMessage() == "Failed to load mock fixture entry bad-1"


def test_add_to_loads_model_fixture(mock_fixtures, service, monkeypatch, tmp_path):
    """`add-to-fixture <model-code>` loads the model's automatic fixture, never the RDM fallback."""
    monkeypatch.setattr(fixtures, "current_app", SimpleNamespace(instance_path=str(tmp_path), config={}))
    monkeypatch.setattr(fixtures, "entry_points", lambda **kwargs: [])
    monkeypatch.setattr(fixtures, "_original_add_to", lambda self, fixture: pytest.fail("RDM fallback used"))
    (tmp_path / "app_data").mkdir()
    (tmp_path / "app_data" / "mock.yaml").write_text(
        "- id: add-1\n  metadata:\n    title: Added\n  files:\n    enabled: false\n"
    )

    fixtures._add_to(FixturesEngine(system_identity), "mock")

    assert _read(service, "add-1")["metadata"] == {"title": "Added"}


def test_adds_published_record_to_community(mock_fixtures, service, monkeypatch):
    """A ``community`` entry adds the record to that community once it is published, without passing it as data."""
    added = []

    def bulk_add(identity, community_id, record_ids):
        # the record must already be published, bulk_add resolves published records only
        added.append((community_id, record_ids, _read(service, record_ids[0])["metadata"]))
        return []

    monkeypatch.setattr(
        loader, "current_rdm_records", SimpleNamespace(record_communities_service=SimpleNamespace(bulk_add=bulk_add))
    )

    mock_fixtures(
        "- id: com-1\n  community: my-community\n  metadata:\n    title: In community\n  files:\n    enabled: false\n"
    )

    assert added == [("my-community", ["com-1"], {"title": "In community"})]
