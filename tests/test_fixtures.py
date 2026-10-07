# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Tests for the automatically registered per-model record fixtures.

These exercise the fixture registry/dispatch logic and the non-draft service path
in isolation (no DB/search) by replacing the runtime registry, the entry-point
lookup and the services. The draft service path runs against the real mock model
in ``test_fixtures_drafts.py``.
"""

from __future__ import annotations

import logging
import threading
from pathlib import Path
from types import SimpleNamespace

import pytest
from flask_principal import Identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_rdm_records.fixtures import FixturesEngine
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import PIDField

from oarepo_runtime import fixtures
from oarepo_runtime.fixtures import loader


class FakeItem:
    """Minimal result item carrying the created record id."""

    def __init__(self, id_: str) -> None:
        """Remember the record id."""
        self.id = id_


class FakeRecord(Record):
    """Record class whose pid provider the fixture swaps during load."""

    pid = PIDField("id", provider=RecordIdProviderV2)


class FakePlainService:
    """Stand-in for a non-draft service: it has no publish method on purpose."""

    record_cls = FakeRecord

    def __init__(self, records: set[str] = frozenset()) -> None:
        """Start with the given existing ids and no created or updated records."""
        self.records = set(records)
        self.created: list[dict] = []
        self.updated: list[tuple] = []

    def read(self, identity, id_):
        """Fail like invenio when the record does not exist."""
        if id_ not in self.records:
            raise PIDDoesNotExistError("recid", id_)

    def update(self, identity, id_, data):
        """Record the update."""
        self.updated.append((id_, data))
        return FakeItem(id_)

    def create(self, identity, data):
        """Record the data and return an item with a generated id."""
        self.created.append(data)
        return FakeItem(f"id-{len(self.created)}")


def _model(code: str, service) -> SimpleNamespace:
    return SimpleNamespace(code=code, service=service, file_service=None)


def _install(monkeypatch, models: list[SimpleNamespace]) -> None:
    runtime = SimpleNamespace(models={model.code: model for model in models})
    monkeypatch.setattr(fixtures, "current_runtime", runtime)
    monkeypatch.setattr(loader, "current_runtime", runtime)


def test_model_record_fixtures_updates_existing_non_draft_record(monkeypatch, tmp_path):
    """An entry whose ``id`` already exists in a plain service is updated, not created."""
    service = FakePlainService(records={"abc"})
    _install(monkeypatch, [_model("article", service)])
    (tmp_path / "article.yaml").write_text("- id: abc\n  metadata:\n    title: A\n")

    fixtures.ModelRecordFixtures("article", tmp_path).load()

    assert service.created == []
    assert service.updated == [("abc", {"metadata": {"title": "A"}})]


def test_model_record_fixtures_leaves_non_draft_records_unpublished(monkeypatch, tmp_path):
    """Publishing is gated on the service being a draft service, so a plain service is never published."""
    service = FakePlainService()
    _install(monkeypatch, [_model("article", service)])
    (tmp_path / "article.yaml").write_text("- metadata:\n    title: A\n")

    fixtures.ModelRecordFixtures("article", tmp_path).load()

    assert service.created == [{"metadata": {"title": "A"}}]


def test_model_record_fixtures_without_data_file_is_a_noop(monkeypatch, tmp_path):
    """Most models ship no fixture data, so a missing file must not create anything or raise."""
    service = FakePlainService()
    _install(monkeypatch, [_model("empty", service)])

    fixtures.ModelRecordFixtures("empty", tmp_path).load()

    assert service.created == []


def test_model_fixtures_excludes_entrypoint_overridden_models(monkeypatch, tmp_path):
    """An entry point named after a model overrides its automatic fixture, so only the rest are built."""
    book = _model("book", FakePlainService())
    article = _model("article", FakePlainService())
    monkeypatch.setattr(fixtures, "current_app", SimpleNamespace(instance_path=str(tmp_path), config={}))
    monkeypatch.setattr(fixtures, "entry_points", lambda **kwargs: [SimpleNamespace(name="book")])
    _install(monkeypatch, [book, article])

    built = fixtures._model_fixtures()

    assert set(built) == {"article"}


@pytest.mark.parametrize("code", sorted(fixtures.INVENIO_MODELS))
def test_model_fixtures_excludes_invenio_handled_models(monkeypatch, tmp_path, code):
    """Invenio loads its own fixtures for these models, so they must not get an automatic one."""
    invenio_model = _model(code, FakePlainService())
    book = _model("book", FakePlainService())
    monkeypatch.setattr(fixtures, "current_app", SimpleNamespace(instance_path=str(tmp_path), config={}))
    monkeypatch.setattr(fixtures, "entry_points", lambda **kwargs: [])
    _install(monkeypatch, [invenio_model, book])

    built = fixtures._model_fixtures()

    assert set(built) == {"book"}


def test_add_to_falls_back_for_unknown_fixture(monkeypatch, tmp_path):
    """A name that is neither an entry point nor a model code must still reach the RDM vocabulary reload."""
    monkeypatch.setattr(fixtures, "current_app", SimpleNamespace(instance_path=str(tmp_path), config={}))
    monkeypatch.setattr(fixtures, "entry_points", lambda **kwargs: [])
    _install(monkeypatch, [])
    called = []
    monkeypatch.setattr(fixtures, "_original_add_to", lambda self, fixture: called.append(fixture))

    fixtures._add_to(FixturesEngine(Identity("test")), "contributorsroles")

    assert called == ["contributorsroles"]


def test_model_record_fixtures_logs_failed_entry_and_continues(monkeypatch, tmp_path, caplog):
    """A failing entry is logged as an error and does not stop the remaining entries from loading."""
    service = FakePlainService()
    original_create = service.create

    def create(identity, data):
        if data["metadata"]["title"] == "bad":
            raise ValueError("boom")
        return original_create(identity, data)

    service.create = create
    _install(monkeypatch, [_model("article", service)])
    (tmp_path / "article.yaml").write_text("- id: bad-1\n  metadata:\n    title: bad\n- metadata:\n    title: good\n")

    with caplog.at_level(logging.ERROR, logger="oarepo_runtime.fixtures"):
        fixtures.ModelRecordFixtures("article", tmp_path).load()

    assert service.created == [{"metadata": {"title": "good"}}]
    [record] = caplog.records
    assert record.levelno == logging.ERROR
    assert record.getMessage() == "Failed to load article fixture entry bad-1"
    assert isinstance(record.exc_info[1], ValueError)


@pytest.mark.parametrize(("env", "lazy"), [("on", True), ("", False)])
def test_model_record_fixtures_offloads_entries_when_lazy(monkeypatch, tmp_path, env, lazy):
    """With INVENIO_LAZY_FIXTURES on, entries go to a worker with picklable args and an absolute fixtures folder."""
    service = FakePlainService()
    _install(monkeypatch, [_model("article", service)])
    monkeypatch.setenv("INVENIO_LAZY_FIXTURES", env)
    delayed = []
    monkeypatch.setattr(fixtures.load_fixture_entry, "delay", lambda *args: delayed.append(args))
    (tmp_path / "data").mkdir()
    (tmp_path / "data" / "article.yaml").write_text("- metadata:\n    title: A\n")
    monkeypatch.chdir(tmp_path)

    fixtures.ModelRecordFixtures("article", Path("data")).load()

    if lazy:
        assert delayed == [("article", str(tmp_path.resolve() / "data"), {"metadata": {"title": "A"}})]
        assert service.created == []
    else:
        assert delayed == []
        assert service.created == [{"metadata": {"title": "A"}}]


@pytest.mark.parametrize(
    ("files", "title"),
    [
        pytest.param({"article.json": '[{"metadata": {"title": "J"}}]'}, "J", id="json"),
        pytest.param(
            {"article.json": '[{"metadata": {"title": "J"}}]', "article.yaml": "- metadata:\n    title: Y\n"},
            "Y",
            id="yaml-wins",
        ),
    ],
)
def test_model_record_fixtures_reads_json_file(monkeypatch, tmp_path, files, title):
    """A JSON fixture file is loaded when there is no YAML one; YAML takes precedence."""
    service = FakePlainService()
    _install(monkeypatch, [_model("article", service)])
    for name, content in files.items():
        (tmp_path / name).write_text(content)

    fixtures.ModelRecordFixtures("article", tmp_path).load()

    assert service.created == [{"metadata": {"title": title}}]


@pytest.mark.parametrize(
    ("config", "expected"),
    [({}, "instance/app_data"), ({"OAREPO_FIXTURES_FOLDER": "/sample-data"}, "/sample-data")],
)
def test_model_fixtures_read_from_configured_folder(monkeypatch, tmp_path, config, expected):
    """OAREPO_FIXTURES_FOLDER replaces the instance's app_data folder for model fixtures and custom loaders."""
    monkeypatch.setattr(fixtures, "current_app", SimpleNamespace(instance_path="instance", config=config))
    monkeypatch.setattr(fixtures, "entry_points", lambda **kwargs: [])
    _install(monkeypatch, [_model("book", FakePlainService())])

    built = fixtures._model_fixtures()

    assert built["book"]._app_data_folder == Path(expected)


def test_pid_provider_swapped_once_for_concurrent_loads():
    """Overlapping loads in parallel threads share one swap: installed by the first, restored by the last."""
    field = FakeRecord.pid.field
    entered, release_first = threading.Event(), threading.Event()
    seen = {}

    def first():
        with loader._fixture_id_provider_installed(field):
            seen["first"] = field._provider
            entered.set()
            release_first.wait(5)

    thread = threading.Thread(target=first)
    thread.start()
    entered.wait(5)
    with loader._fixture_id_provider_installed(field):
        seen["second"] = field._provider
    seen["after_second"] = field._provider
    release_first.set()
    thread.join(5)

    assert seen["first"] is seen["second"] is seen["after_second"]
    assert issubclass(seen["first"], RecordIdProviderV2)
    assert seen["first"] is not RecordIdProviderV2
    assert field._provider is RecordIdProviderV2
    assert loader._provider_users == {}


@pytest.mark.parametrize(
    ("records", "members", "errors", "added", "logged"),
    [
        pytest.param(set(), set(), [], True, False, id="created-added-without-check"),
        pytest.param({"abc"}, {"com-uuid"}, [], False, False, id="updated-already-member"),
        pytest.param({"abc"}, set(), [], True, False, id="updated-not-member"),
        pytest.param(set(), set(), [{"message": "boom"}], True, True, id="bulk-add-failed"),
    ],
)
def test_model_record_fixtures_adds_record_to_community(
    monkeypatch, tmp_path, caplog, records, members, errors, added, logged
):
    """A created record is added to the community; an updated one only if it is not already a member."""
    service = FakePlainService(records=records)
    record = SimpleNamespace(parent=SimpleNamespace(communities=members))
    item = SimpleNamespace(id="abc", _record=record)
    service.create = lambda identity, data: item
    service.update = lambda identity, id_, data: item
    _install(monkeypatch, [_model("article", service)])
    community_cls = SimpleNamespace(pid=SimpleNamespace(resolve=lambda slug: "com-uuid"))
    communities_service = SimpleNamespace(record_cls=community_cls)
    monkeypatch.setattr(loader, "current_communities", SimpleNamespace(service=communities_service))
    calls = []

    def bulk_add(identity, community_id, record_ids):
        calls.append((community_id, record_ids))
        return errors

    monkeypatch.setattr(
        loader, "current_rdm_records", SimpleNamespace(record_communities_service=SimpleNamespace(bulk_add=bulk_add))
    )
    (tmp_path / "article.yaml").write_text("- id: abc\n  community: my-community\n  metadata:\n    title: A\n")

    with caplog.at_level(logging.ERROR, logger="oarepo_runtime.fixtures"):
        fixtures.ModelRecordFixtures("article", tmp_path).load()

    assert calls == ([("my-community", ["abc"])] if added else [])
    assert bool(caplog.records) == logged


def _engine_env(monkeypatch, tmp_path, eps):
    monkeypatch.setattr(fixtures, "current_app", SimpleNamespace(instance_path=str(tmp_path), config={}))
    monkeypatch.setattr(fixtures, "entry_points", lambda **kwargs: eps)


def test_add_to_runs_custom_loader_instead_of_model_fixture(monkeypatch, tmp_path):
    """An ``oarepo.fixtures`` entry point named after the fixture is called with the identity and fixtures folder."""
    called = []

    class Loader:
        def __init__(self, search_paths, filename):
            self.search_paths = search_paths
            self.filename = filename

        def load(self):
            called.append((self.search_paths, self.filename))

    loader_ep = SimpleNamespace(name="book", load=lambda: Loader)
    _engine_env(monkeypatch, tmp_path, [loader_ep])
    _install(monkeypatch, [_model("book", FakePlainService())])
    monkeypatch.setattr(fixtures, "_original_add_to", lambda self, fixture: pytest.fail("RDM fallback used"))
    identity = Identity("test")

    fixtures._add_to(FixturesEngine(identity), "book")

    assert called == [([tmp_path / "app_data"], "book.yaml")]


def test_run_loads_rdm_fixtures_custom_loaders_and_model_fixtures(monkeypatch, tmp_path):
    """``rdm-records fixtures`` runs the RDM fixtures, every custom loader and the remaining model fixtures."""
    calls = []

    class Loader:
        def __init__(self, search_paths, filename):
            self.search_paths = search_paths
            self.filename = filename

        def load(self):
            calls.append("custom book")

    loader_ep = SimpleNamespace(name="book", load=lambda: Loader)
    _engine_env(monkeypatch, tmp_path, [loader_ep])
    article = FakePlainService()
    _install(monkeypatch, [_model("book", FakePlainService()), _model("article", article)])
    monkeypatch.setattr(fixtures, "_original_run", lambda self: calls.append("rdm"))
    (tmp_path / "app_data").mkdir()
    (tmp_path / "app_data" / "article.yaml").write_text("- metadata:\n    title: A\n")

    fixtures._run(FixturesEngine(Identity("test")))

    assert calls == ["rdm", "custom book"]
    assert article.created == [{"metadata": {"title": "A"}}]
