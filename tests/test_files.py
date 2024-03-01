import tempfile
from io import BytesIO
from pathlib import Path

from oarepo_runtime.datastreams.fixtures import dump_fixtures, load_fixtures, FixturesCallback
from oarepo_runtime.datastreams.types import StatsKeepingDataStreamCallback
from oarepo_runtime.datastreams.utils import get_file_service_for_record_class
from records2.proxies import current_service
from records2.records.api import Records2Record
from tests.test_fixtures import read_yaml


def test_dump_with_files(db, app, identity, search_clear, location):
    rec = current_service.create(identity, {"metadata": {"title": "blah"}})
    data = (
        Path(__file__).parent / "file_data" / "files" / "001" / "data" / "test.png"
    ).read_bytes()
    add_file_to_record(
        app.extensions["records2"].service_files,
        rec.id,
        "test.png",
        identity,
        data=data,
    )
    add_file_to_record(
        app.extensions["records2"].service_files,
        rec.id,
        "another.png",
        identity,
        data=data,
    )

    rec2 = current_service.create(identity, {"metadata": {"title": "blah 2"}})
    add_file_to_record(
        app.extensions["records2"].service_files,
        rec2.id,
        "test.png",
        identity,
        data=data,
    )
    Records2Record.index.refresh()

    with tempfile.TemporaryDirectory() as fixture_dir:
        callback = FixturesCallback()
        dump_fixtures(fixture_dir, use_files=True, callback=callback)
        assert callback.ok_entries_count == 2
        assert callback.failed_entries_count == 0
        assert callback.filtered_entries_count == 0
        fixture_dir = Path(fixture_dir)

        assert read_yaml(fixture_dir / "catalogue.yaml")["records2"] == [
            {"writer": "service", "service": "records2"},
            {"writer": "attachments_service", "service": "records2"},
            {"source": "records2.yaml"},
        ]

        assert set(
            x["metadata"]["title"] for x in read_yaml(fixture_dir / "records2.yaml")
        ) == {"blah", "blah 2"}

        assert (fixture_dir / "files" / "001" / "data" / "test.png").exists()
        assert (fixture_dir / "files" / "001" / "data" / "another.png").exists()
        assert (fixture_dir / "files" / "002" / "data" / "test.png").exists()


# taken from https://github.com/inveniosoftware/invenio-records-resources/blob/master/tests/services/files/files_utils.py
def add_file_to_record(file_service, recid, file_id, identity, data=None):
    """Add a file to the record."""
    file_service.init_files(identity, recid, data=[{"key": file_id}])
    file_service.set_file_content(
        identity,
        recid,
        file_id,
        BytesIO(data or (b"test file content: " + file_id.encode("utf-8"))),
    )
    result = file_service.commit_file(identity, recid, file_id)
    return result


def test_load_with_files(db, app, identity, search_clear, location):
    callback = FixturesCallback(log_error_entry=True)
    load_fixtures(Path(__file__).parent / "file_data", callback=callback)
    assert callback.ok_entries_count == 2
    assert callback.failed_entries_count == 0
    assert callback.filtered_entries_count == 0

    # list records
    Records2Record.index.refresh()
    results = list(current_service.scan(identity, params={"order": "created"}))
    assert len(results) == 2

    # get record #1 and check files
    file_service = get_file_service_for_record_class(Records2Record)
    first_record_list = list(
        file_service.list_files(identity, results[0]["id"]).entries
    )
    assert len(first_record_list) == 2
    first_item = next(x for x in first_record_list if x["key"] == "test.png")
    assert first_item["size"] == 822
    with file_service.get_file_content(
        identity, results[0]["id"], "test.png"
    ).open_stream("rb") as f:
        assert f.read()[:5] == b"\x89PNG\r"
