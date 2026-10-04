# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Tests for the model record fixtures running against the real draft service of the mock model."""

from __future__ import annotations

import hashlib
import logging
from contextlib import contextmanager
from io import BytesIO
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


def test_downloads_fetch_files_before_publishing(mock_fixtures, service, monkeypatch):
    """A fetch file is downloaded by the fixture, so the record is published without waiting for a worker."""

    @contextmanager
    def fake_get(url, **kwargs):
        assert url == "https://example.org/f.txt"
        yield SimpleNamespace(raise_for_status=lambda: None, raw=BytesIO(b"fetched"))

    monkeypatch.setattr(loader.requests, "get", fake_get)

    mock_fixtures(
        "- id: fet-1\n"
        "  metadata:\n"
        "    title: Fetched\n"
        "  files:\n"
        "    entries:\n"
        "      - key: f.txt\n"
        "        size: 7\n"
        f"        checksum: {_md5(b'fetched')}\n"
        "        transfer:\n"
        "          type: F\n"
        "          url: https://example.org/f.txt\n"
    )

    record_file = _files(service.files, "fet-1")["f.txt"]
    assert (record_file["size"], record_file["checksum"]) == (7, _md5(b"fetched"))
    assert record_file["transfer"]["type"] == "L"


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
