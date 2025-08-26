from pathlib import Path

import pytest
from flask_security import login_user
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session
from invenio_records_permissions.generators import AnyUser, AuthenticatedUser
from invenio_records_resources.services.errors import PermissionDeniedError
from thesis.records.api import ThesisDraft, ThesisRecord

from oarepo_runtime.services.generators import RecordOwners
from tests.test_files import add_file_to_record


@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location


@pytest.fixture()
def service():
    from thesis.proxies import current_service

    return current_service


@pytest.fixture()
def service_config():
    from thesis.services.records.config import ThesisServiceConfig

    return ThesisServiceConfig


@pytest.fixture()
def owners_permissions():
    from invenio_records_permissions.policies.records import RecordPermissionPolicy

    ret = type(
        "OwnersPermissionPolicy",
        (RecordPermissionPolicy,),
        dict(
            can_create=[AnyUser()],
            can_read_draft=[RecordOwners()],
            can_update_draft=[RecordOwners()],
            can_search_drafts=[AuthenticatedUser()],
            can_publish=[AuthenticatedUser()],
        ),
    )
    return ret


@pytest.fixture()
def patch_owner_permissions(service, monkeypatch, service_config, owners_permissions):
    monkeypatch.setattr(service_config, "PERMISSIONS_PRESETS", ["read_only"])
    monkeypatch.setattr(
        service_config, "base_permission_policy_cls", owners_permissions
    )


def test_owners(app, service, identity, users, search_clear):
    rec = service.create(identity, data={"metadata": {"title": "blah"}})
    assert len(rec._obj.parent.owners.to_dict()) == 1
    assert "owners" not in rec.data["parent"]
    record_id = rec.data["id"]
    updated_rec1 = service.update_draft(
        users[1].identity, id_=record_id, data={"metadata": {"title": "blahblah"}}
    )
    assert len(updated_rec1._obj.parent.owners.to_dict()) == 2
    updated_read = service.read_draft(identity, id_=record_id)
    assert len(updated_read._obj.parent.owners.to_dict()) == 2
    updated_rec2 = service.update_draft(
        users[1].identity, id_=record_id, data={"metadata": {"title": "blahblah"}}
    )
    assert len(updated_rec2._obj.parent.owners.to_dict()) == 2
    # publish
    data = (
        Path(__file__).parent / "file_data" / "files" / "001" / "data" / "test.png"
    ).read_bytes()
    add_file_to_record(
        app.extensions["thesis"].service_draft_files,
        rec.id,
        "test.png",
        identity,
        data=data,
    )
    publish_res = service.publish(system_identity, id_=record_id)
    published = service.read(identity, id_=record_id)
    assert len(published._obj.parent.owners.to_dict()) == 2
    updated_rec = service.new_version(users[2].identity, id_=record_id)
    assert len(updated_rec._obj.parent.owners.to_dict()) == 2
    updated_rec = service.update_draft(
        users[2].identity,
        id_=updated_rec.data["id"],
        data={"metadata": {"title": "blahblah"}},
    )
    assert len(updated_rec._obj.parent.owners.to_dict()) == 3


# it's prob the location fixture doing database problems in debug mode for some reason
def test_permissions(
    service,
    users,
    patch_owner_permissions,
    search_clear,
):
    identity1 = users[0].identity
    identity2 = users[1].identity

    rec = service.create(identity1, data={"metadata": {"title": "blah"}})
    id_ = rec.data["id"]
    read_owner = service.read_draft(identity1, id_)

    with pytest.raises(PermissionDeniedError):
        read_nonowner = service.read_draft(identity2, id_)
    with pytest.raises(PermissionDeniedError):
        service.update_draft(
            identity2, id_=id_, data={"metadata": {"title": "blahblah"}}
        )

    update = service.update_draft(
        identity1, id_=id_, data={"metadata": {"title": "blahblah"}}
    )
    read = service.read_draft(identity1, id_)
    assert read.data["metadata"]["title"] == "blahblah"


def _test_search_mixed(users, logged_client):
    BASE_URL = "/thesis/"
    user1_client = logged_client(users[1])
    user2_client = logged_client(users[2])

    draft1 = user1_client.post(
        BASE_URL,
        json={"metadata": {"title": "draft1-1"}, "files": {"enabled": False}},
    )
    draft2 = user1_client.post(BASE_URL, json={"metadata": {"title": "draft1-2"}})
    draft3 = user2_client.post(BASE_URL, json={"metadata": {"title": "draft2-1"}})
    publish1 = user1_client.post(f"{BASE_URL}{draft1.json['id']}/draft/actions/publish")
    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()
    search_2 = user1_client.get(f"/user{BASE_URL}").json["hits"]["hits"]
    assert set([obj["id"] for obj in search_2]) == {
        draft1.json["id"],
        draft2.json["id"],
    }
    assert (
        len([obj["id"] for obj in search_2 if obj["links"]["self"].endswith("/draft")])
        == 1
    )


def test_search_drafts(users, logged_client, search_clear):
    BASE_URL = "/thesis/"
    user1_client = logged_client(users[1])
    user2_client = logged_client(users[2])

    draft1 = user1_client.post(BASE_URL, json={"metadata": {"title": "draft1-1"}})
    draft2 = user1_client.post(BASE_URL, json={"metadata": {"title": "draft1-2"}})
    draft3 = user2_client.post(BASE_URL, json={"metadata": {"title": "draft2-1"}})

    def get_ids(result):
        return [x["id"] for x in result["hits"]["hits"]]

    ThesisDraft.index.refresh()
    search_1 = user1_client.get(f"/user{BASE_URL}")
    search_2 = user2_client.get(f"/user{BASE_URL}")
    assert len(search_1.json["hits"]["hits"]) == 2
    search_1_ids = get_ids(search_1.json)
    assert draft1.json["id"] in search_1_ids
    assert draft2.json["id"] in search_1_ids

    assert len(search_2.json["hits"]["hits"]) == 1
    search_2_ids = get_ids(search_2.json)
    assert draft3.json["id"] in search_2_ids


def test_drafts_published_mixed(users, logged_client, search_clear):
    _test_search_mixed(users, logged_client)


def test_drafts_published_mixed_with_permissions(
    users, logged_client, patch_owner_permissions, search_clear
):
    _test_search_mixed(users, logged_client)
