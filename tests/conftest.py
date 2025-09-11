#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
# Parts of this file are based on tests in Invenio-Records-Resources.
# https://github.com/inveniosoftware/invenio-records-resources/blob/master/tests/conftest.py
#
#
"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""

from __future__ import annotations

import pytest
from flask_principal import Identity, Need, UserNeed
from flask_security import login_user
from flask_security.utils import hash_password
from invenio_access import ActionUsers, current_access
from invenio_accounts.proxies import current_datastore
from invenio_accounts.testutils import login_user_via_session
from invenio_app.factory import create_api as _create_api
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime.info.views import InfoResource, InfoConfig
from oarepo_runtime.services.records.mapping import update_all_records_mappings

pytest_plugins = ("celery.contrib.pytest",)


@pytest.fixture(scope="module")
def app_config(app_config):
    """Override pytest-invenio app_config fixture.

    Needed to set the fields on the custom fields schema.
    """
    app_config["FILES_REST_STORAGE_CLASS_LIST"] = {
        "L": "Local",
    }

    app_config["FILES_REST_DEFAULT_STORAGE_CLASS"] = "L"

    app_config["RECORDS_REFRESOLVER_CLS"] = "invenio_records.resolver.InvenioRefResolver"
    app_config["RECORDS_REFRESOLVER_STORE"] = "invenio_jsonschemas.proxies.current_refresolver_store"

    app_config["THEME_FRONTPAGE"] = False

    # only API app is running
    app_config["SITE_API_URL"] = "https://127.0.0.1:5000/"
    app_config["SERVER_NAME"] = "127.0.0.1:5000"
    app_config["PREFERRED_URL_SCHEME"] = "https"

    return app_config


@pytest.fixture(scope="module")
def extra_entry_points():
    """Extra entry points."""
    return {}


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_api


@pytest.fixture(scope="module")
def identity_simple():
    """Create a simple identity."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(Need(method="system_role", value="any_user"))
    i.provides.add(Need(method="system_role", value="authenticated_user"))
    return i


@pytest.fixture(scope="module")
def search_with_field_mapping(app, search):
    """Search fixture."""
    # Ensure all record mappings are updated
    update_all_records_mappings()
    return search


@pytest.fixture(scope="module")
def service(app):
    return current_service_registry.get("mock-record-service")

@pytest.fixture()
def admin_role(app, db):
    """Create some roles."""
    with db.session.begin_nested():
        datastore = app.extensions["security"].datastore
        role = datastore.create_role(name="admin", description="admin role")

    db.session.commit()
    return role

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
def client_with_credentials_admin(db, client, user, admin_role):
    """Log in a user to the client with admin role. This role does not have defined facets."""

    current_datastore.add_role_to_user(user, admin_role)
    action = current_access.actions["superuser-access"]
    db.session.add(ActionUsers.allow(action, user_id=user.id))

    login_user(user, remember=True)
    login_user_via_session(client, email=user.email)

    return client


@pytest.fixture()
def info_blueprint(app):
    app.register_blueprint(InfoResource(InfoConfig(app)).as_blueprint())

