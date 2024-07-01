# -*- coding: utf-8 -*-
#
# Copyright (C) 2020 CERN.
# Copyright (C) 2021 TU Wien.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""
import logging
import os
from pathlib import Path
from typing import Union

import pytest
from flask_principal import Identity, Need, RoleNeed, UserNeed
from flask_security import login_user
from flask_security.utils import hash_password
from invenio_access import ActionUsers, current_access
from invenio_access.permissions import any_user, authenticated_user, system_process
from invenio_accounts.proxies import current_datastore
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api as _create_api

from oarepo_runtime.datastreams import BaseTransformer, BaseWriter, StreamBatch
from oarepo_runtime.datastreams.fixtures import FixturesCallback
from oarepo_runtime.datastreams.types import DataStreamCallback
from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices

pytest_plugins = ("celery.contrib.pytest",)


logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s %(levelname)s [%(threadName)s] %(name)s %(message)s",
)
# logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)
logging.getLogger("celery").setLevel(logging.DEBUG)


@pytest.fixture(scope="module")
def h():
    """Accept JSON headers."""
    return {"accept": "application/json"}


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points to load the mock_module features."""
    return {
        "oarepo.fixtures": ["1000-test = tests.pkg_data"],
        "invenio_i18n.translations": ["1000-test = tests"],
    }


class StatusTransformer(BaseTransformer):
    def apply(self, batch: StreamBatch, *args, **kwargs):
        for stream_entry in batch.entries:
            if "ok" in stream_entry.entry:
                stream_entry.entry.pop("ok")
            if "skipped" in stream_entry.entry:
                stream_entry.filtered = True
        return batch


class FailingWriter(BaseWriter):
    def write(self, batch: StreamBatch) -> Union[StreamBatch, None]:
        raise Exception("Failing writer")


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"
    app_config["I18N_LANGUAGES"] = [("en", "English"), ("cs", "Czech")]
    app_config["BABEL_DEFAULT_LOCALE"] = "en"

    app_config["DATASTREAMS_TRANSFORMERS"] = {
        "status": StatusTransformer,
    }
    app_config["SEARCH_HOSTS"] = [
        {
            "host": os.environ.get("OPENSEARCH_HOST", "localhost"),
            "port": os.environ.get("OPENSEARCH_PORT", "9200"),
        }
    ]
    # for files
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
        "F": "Fetch",
        "R": "Remote",
    }
    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"
    app_config["DATASTREAMS_WRITERS"] = {"failing": FailingWriter}

    app_config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:?check_same_thread=False"

    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    return i


@pytest.fixture()
def identity_with_role(app, db, user):
    """Simple identity fixture."""
    i = Identity(1)

    i.provides.add(UserNeed(user.id))
    i.provides.add(RoleNeed("myrole"))
    i.provides.add(Need(method="system_role", value="any_user"))
    return i


@pytest.fixture(scope="module")
def identity():
    """Simple identity to interact with the service."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(any_user)
    i.provides.add(system_process)
    return i


@pytest.fixture(scope="module")
def more_identities():
    """Simple identity to interact with the service."""
    i2 = Identity(2)
    i2.provides.add(UserNeed(2))
    i2.provides.add(any_user)
    i2.provides.add(authenticated_user)

    i3 = Identity(3)
    i3.provides.add(UserNeed(3))
    i3.provides.add(any_user)
    i3.provides.add(authenticated_user)

    return [i2, i3]


@pytest.fixture(scope="module")
def non_system_identity():
    """Simple identity to interact with the service."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(any_user)
    return i


@pytest.fixture()
def custom_fields():
    prepare_cf_indices()


@pytest.fixture()
def user(app, db):
    """Create example user."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        _user = datastore.create_user(
            email="info@inveniosoftware.org",
            password=hash_password("password"),
            active=True,
        )
    db.session.commit()
    return _user


"""
@pytest.fixture(scope="module", autouse=True)
def location(location):
    return location
"""


@pytest.fixture()
def more_users(app, db, user):
    """Create example user."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        user2 = datastore.create_user(
            email="user_two@cesnet.cz",
            password=hash_password("password"),
            active=True,
        )
        datastore = app.extensions["security"].datastore
        user3 = datastore.create_user(
            email="user_three@cesnet.cz",
            password=hash_password("password"),
            active=True,
        )
    db.session.commit()
    return [user, user2, user3]


@pytest.fixture()
def admin_role(app, db):
    """Create some roles."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        role = datastore.create_role(name="admin", description="admin role")

    db.session.commit()
    return role


@pytest.fixture()
def curator_role(app, db):
    """Create some roles."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        role = datastore.create_role(name="curator", description="curator role")

    db.session.commit()
    return role


@pytest.fixture()
def client_with_credentials_admin(db, client, user, admin_role):
    """Log in a user to the client with admin role. This role does not have defined facets."""

    current_datastore.add_role_to_user(user, admin_role)
    action = current_access.actions["superuser-access"]
    db.session.add(ActionUsers.allow(action, user_id=user.id))

    login_user(user, remember=True)
    login_user_via_session(client, email=user.email)

    return client


@pytest.fixture()
def client_with_credentials_curator(db, client, user, curator_role):
    """Log in a user to the client with curator role. This role has defined facets."""

    current_datastore.add_role_to_user(user, curator_role)
    action = current_access.actions["superuser-access"]
    db.session.add(ActionUsers.allow(action, user_id=user.id))

    login_user(user, remember=True)
    login_user_via_session(client, email=user.email)

    return client


@pytest.fixture()
def sample_data(db, app, identity, search_clear, location):
    from records2.proxies import current_service
    from records2.records.api import Records2Record

    from oarepo_runtime.datastreams.fixtures import load_fixtures

    load_fixtures(Path(__file__).parent / "data", callback=FixturesCallback())
    Records2Record.index.refresh()
    titles = set()
    for rec in current_service.scan(identity):
        titles.add(rec["metadata"]["title"])
    assert titles == {"record 1", "record 2"}


@pytest.fixture()
def sample_data_system_field(db, app, identity, search_clear, location):
    from records2.proxies import current_service
    from records2.records.api import Records2Record

    from oarepo_runtime.datastreams.fixtures import load_fixtures

    load_fixtures(
        Path(__file__).parent / "data_system_field", callback=FixturesCallback()
    )
    Records2Record.index.refresh()
    titles = set()
    for rec in current_service.scan(identity):
        titles.add(rec["metadata"]["title"])
    assert titles == {"record 1", "record 2"}
