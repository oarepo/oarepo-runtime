from io import BytesIO
from pathlib import Path

from invenio_access.permissions import system_identity
from records2.proxies import current_service


# taken from https://github.com/inveniosoftware/invenio-records-resources/blob/master/tests/services/files/files_utils.py
def add_file_to_record(
    file_service, recid, file_id, identity, data=None, featured=None
):
    """Add a file to the record."""
    if featured:
        file_service.init_files(
            identity, recid, data=[{"key": file_id, "metadata": {"featured": True}}]
        )

    else:
        file_service.init_files(identity, recid, data=[{"key": file_id}])
    file_service.set_file_content(
        identity,
        recid,
        file_id,
        BytesIO(data or (b"test file content: " + file_id.encode("utf-8"))),
    )
    result = file_service.commit_file(identity, recid, file_id)
    return result


def test_create_rec_with_files(db, app, identity, search_clear, location):
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
        featured=True,
    )
    # current_service.scan(system_identity)
    # current_service.read(system_identity, rec.id)

    # Records2Record.index.refresh()
    res = current_service.read(system_identity, rec.id)
    assert "featured" in res.data["metadata"]
    print("record", res.data["metadata"])
