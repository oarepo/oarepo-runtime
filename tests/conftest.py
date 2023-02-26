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


import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_access.permissions import any_user, system_process
from invenio_app.factory import create_app as _create_app

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
        "invenio_base.api_apps": ["records2 = records2.ext:Records2Ext"],
        "invenio_base.apps": ["records2 = records2.ext:Records2Ext"],
        "invenio_db.alembic": ["records2 = records2:alembic"],
        "invenio_db.models": ["records2 = records2.records.models"],
        "invenio_base.api_blueprints": [
            "records2 = records2.views:create_blueprint_from_app_records2"
        ],
        "invenio_base.blueprints": [
            "records2 = records2.views:create_blueprint_from_app_records2"
        ],
        "invenio_search.mappings": ["records2 = records2.records.mappings"],
        "invenio_jsonschemas.schemas": ["records2 = records2.records.jsonschemas"],
    }


@pytest.fixture(scope="module")
def app_config(app_config):
    """Mimic an instance's configuration."""
    app_config["JSONSCHEMAS_HOST"] = "localhost"
    app_config["BABEL_DEFAULT_LOCALE"] = "en"
    app_config["I18N_LANGUAGES"] = [("da", "Danish")]
    app_config[
        "RECORDS_REFRESOLVER_CLS"
    ] = "invenio_records.resolver.InvenioRefResolver"
    app_config[
        "RECORDS_REFRESOLVER_STORE"
    ] = "invenio_jsonschemas.proxies.current_refresolver_store"

    return app_config


@pytest.fixture(scope="module")
def create_app(instance_path, entry_points):
    """Application factory fixture."""
    return _create_app


@pytest.fixture(scope="module")
def identity_simple():
    """Simple identity fixture."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
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
