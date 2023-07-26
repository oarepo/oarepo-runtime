import tempfile
from io import BytesIO
from pathlib import Path

from oarepo_runtime.datastreams.fixtures import dump_fixtures
from records2.records2.proxies import current_service
from records2.records2.records.api import Records2Record
from tests.test_fixtures import read_yaml


def test_dump_with_files(db, app, identity, search_clear, location):
    rec = current_service.create(identity, {'metadata': {'title': 'blah'}})
    add_file_to_record(app.extensions["records2"].service_files, rec.id, 'test.png', identity)
    add_file_to_record(app.extensions["records2"].service_files, rec.id, 'another.png', identity)

    rec2 = current_service.create(identity, {'metadata': {'title': 'blah 2'}})
    add_file_to_record(app.extensions["records2"].service_files, rec2.id, 'test.png', identity)
    Records2Record.index.refresh()

    with tempfile.TemporaryDirectory() as fixture_dir:
        ret = dump_fixtures(fixture_dir, use_files=True)
        assert ret.ok_count == 2
        assert ret.failed_count == 0
        assert ret.skipped_count == 0
        fixture_dir = Path(fixture_dir)

        assert read_yaml(fixture_dir / "catalogue.yaml") == {
            "records2": [{"service": "records2"}, {"source": "records2.yaml"}]
        }
        assert set(
            x["metadata"]["title"] for x in read_yaml(fixture_dir / "records2.yaml")
        ) == {"blah", "blah 2"}


# taken from https://github.com/inveniosoftware/invenio-records-resources/blob/master/tests/services/files/files_utils.py
def add_file_to_record(file_service, recid, file_id, identity):
    """Add a file to the record."""
    file_service.init_files(identity, recid, data=[{"key": file_id}])
    file_service.set_file_content(
        identity, recid, file_id, BytesIO(b"test file content: " + file_id.encode('utf-8'))
    )
    result = file_service.commit_file(identity, recid, file_id)
    return result