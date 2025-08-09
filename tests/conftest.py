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
from __future__ import annotations

"""Pytest configuration.

See https://pytest-invenio.readthedocs.io/ for documentation on which test
fixtures are available.
"""


import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_app.factory import create_api as _create_api
from invenio_records_resources.proxies import current_service_registry

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
