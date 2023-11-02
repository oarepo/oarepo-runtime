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
import os

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_access.permissions import any_user, system_process
from invenio_app.factory import create_api as _create_api

from flask_security import login_user
from flask_security.utils import hash_password
from invenio_access import ActionUsers, current_access
from invenio_accounts.proxies import current_datastore
from invenio_accounts.testutils import login_user_via_session

from oarepo_runtime.datastreams.datastreams import StreamEntry
from oarepo_runtime.datastreams.transformers import BaseTransformer

from pathlib import Path

pytest_plugins = ("celery.contrib.pytest",)


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
    def apply(self, stream_entry: StreamEntry, *args, **kwargs):
        if "ok" in stream_entry.entry:
            stream_entry.entry.pop("ok")
            return stream_entry
        if "skipped" in stream_entry.entry:
            stream_entry.filtered = True
        return stream_entry


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
    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api

@pytest.fixture(scope="module")
def identity():
    """Simple identity to interact with the service."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(any_user)
    i.provides.add(system_process)
    return i

@pytest.fixture(scope="module")
def role_identity():
    """Simple identity to interact with the service that has the role for restricted facets tests."""
    i = Identity(2)
    i.provides.add(any_user)
    i.provides.add(Need(method="role", value="admin"))
    return i

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


@pytest.fixture()
def role(app, db):
    """Create some roles."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        role = datastore.create_role(name="admin", description="admin role")

    db.session.commit()
    return role


@pytest.fixture()
def client_with_credentials(db, client, user, role):
    """Log in a user to the client."""

    current_datastore.add_role_to_user(user, role)
    action = current_access.actions["superuser-access"]
    db.session.add(ActionUsers.allow(action, user_id=user.id))

    login_user(user, remember=True)
    login_user_via_session(client, email=user.email)

    return client

@pytest.fixture()
def sample_data_role_id(db, app, role_identity, search_clear, location):
    from oarepo_runtime.datastreams.fixtures import load_fixtures
    from records2.proxies import current_service
    from records2.records.api import Records2Record
    
    ret = load_fixtures(Path(__file__).parent / "data")
    assert ret.ok_count == 2
    assert ret.failed_count == 0
    assert ret.skipped_count == 0
    Records2Record.index.refresh()
    titles = set()
    for rec in current_service.scan(role_identity):
        titles.add(rec["metadata"]["title"])
    assert titles == {"record 1", "record 2"}

@pytest.fixture()
def sample_data_default_id(db, app, identity, search_clear, location):
    from oarepo_runtime.datastreams.fixtures import load_fixtures
    from records2.proxies import current_service
    from records2.records.api import Records2Record
    
    ret = load_fixtures(Path(__file__).parent / "data")
    assert ret.ok_count == 2
    assert ret.failed_count == 0
    assert ret.skipped_count == 0
    Records2Record.index.refresh()
    titles = set()
    for rec in current_service.scan(identity):
        titles.add(rec["metadata"]["title"])
    assert titles == {"record 1", "record 2"}