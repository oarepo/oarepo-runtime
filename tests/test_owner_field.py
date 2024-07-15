from pathlib import Path

import pytest
from flask_security import login_user
from invenio_access.permissions import system_identity
from invenio_accounts.testutils import login_user_via_session
from invenio_records_permissions.generators import AnyUser, AuthenticatedUser
from invenio_records_resources.services.errors import PermissionDeniedError

from oarepo_runtime.services.generators import RecordOwners
from tests.test_files import add_file_to_record
from thesis.records.api import ThesisDraft, ThesisRecord


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


@pytest.fixture()
def client_logged_as(client, more_users):
    """Logs in a user to the client."""

    def log_user(user_email):
        """Log the user."""
        available_users = more_users

        user = next((u for u in available_users if u.email == user_email), None)
        login_user(user, remember=True)
        login_user_via_session(client, email=user_email)
        return client

    return log_user


@pytest.fixture()
def logged_client_request(client_logged_as):
    def _logged_client_post(user, method, *args, **kwargs):
        applied_client = client_logged_as(user.email)
        return getattr(applied_client, method)(*args, **kwargs)

    return _logged_client_post


def test_owners(app, service, identity, more_users, more_identities, search_clear):
    rec = service.create(identity, data={"metadata": {"title": "blah"}})
    assert len(rec._obj.parent.owners.to_dict()) == 1
    assert "owners" not in rec.data["parent"]
    record_id = rec.data["id"]
    updated_rec1 = service.update_draft(
        more_identities[0], id_=record_id, data={"metadata": {"title": "blahblah"}}
    )
    assert len(updated_rec1._obj.parent.owners.to_dict()) == 2
    updated_read = service.read_draft(identity, id_=record_id)
    assert len(updated_read._obj.parent.owners.to_dict()) == 2
    updated_rec2 = service.update_draft(
        more_identities[0], id_=record_id, data={"metadata": {"title": "blahblah"}}
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
    updated_rec = service.new_version(more_identities[1], id_=record_id)
    assert len(updated_rec._obj.parent.owners.to_dict()) == 2
    updated_rec = service.update_draft(
        more_identities[1],
        id_=updated_rec.data["id"],
        data={"metadata": {"title": "blahblah"}},
    )
    assert len(updated_rec._obj.parent.owners.to_dict()) == 3


# it's prob the location fixture doing database problems in debug mode for some reason
def test_permissions(
    service,
    more_users,
    more_identities,
    patch_owner_permissions,
    search_clear,
):
    identity1 = more_identities[0]
    identity2 = more_identities[1]

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


def _test_search_mixed(more_users, logged_client_request):
    BASE_URL = "/thesis/"
    user1 = more_users[0]
    user2 = more_users[1]

    draft1 = logged_client_request(
        user1,
        "post",
        BASE_URL,
        json={"metadata": {"title": "draft1-1"}, "files": {"enabled": False}},
    )
    draft2 = logged_client_request(
        user1, "post", BASE_URL, json={"metadata": {"title": "draft1-2"}}
    )
    draft3 = logged_client_request(
        user2, "post", BASE_URL, json={"metadata": {"title": "draft2-1"}}
    )
    publish1 = logged_client_request(
        user1, "post", f"{BASE_URL}{draft1.json['id']}/draft/actions/publish"
    )
    ThesisRecord.index.refresh()
    ThesisDraft.index.refresh()
    search_2 = logged_client_request(user1, "get", f"/user{BASE_URL}").json["hits"][
        "hits"
    ]
    assert set([obj["id"] for obj in search_2]) == {
        draft1.json["id"],
        draft2.json["id"],
    }
    assert (
        len([obj["id"] for obj in search_2 if obj["links"]["self"].endswith("/draft")])
        == 1
    )


def test_search_drafts(more_users, logged_client_request, search_clear):
    BASE_URL = "/thesis/"
    user1 = more_users[1]
    user2 = more_users[2]

    draft1 = logged_client_request(
        user1, "post", BASE_URL, json={"metadata": {"title": "draft1-1"}}
    )
    draft2 = logged_client_request(
        user1, "post", BASE_URL, json={"metadata": {"title": "draft1-2"}}
    )
    draft3 = logged_client_request(
        user2, "post", BASE_URL, json={"metadata": {"title": "draft2-1"}}
    )

    def get_ids(result):
        return [x["id"] for x in result["hits"]["hits"]]

    ThesisDraft.index.refresh()
    search_1 = logged_client_request(user1, "get", f"/user{BASE_URL}")
    search_2 = logged_client_request(user2, "get", f"/user{BASE_URL}")
    assert len(search_1.json["hits"]["hits"]) == 2
    search_1_ids = get_ids(search_1.json)
    assert draft1.json["id"] in search_1_ids
    assert draft2.json["id"] in search_1_ids

    assert len(search_2.json["hits"]["hits"]) == 1
    search_2_ids = get_ids(search_2.json)
    assert draft3.json["id"] in search_2_ids


def test_drafts_published_mixed(more_users, logged_client_request, search_clear):
    _test_search_mixed(more_users, logged_client_request)


def test_drafts_published_mixed_with_permissions(
    more_users, logged_client_request, patch_owner_permissions, search_clear
):
    _test_search_mixed(more_users, logged_client_request)
