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
from invenio_app.factory import create_api as _create_api

from oarepo_runtime.datastreams.datastreams import StreamEntry
from oarepo_runtime.datastreams.transformers import BaseTransformer

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
