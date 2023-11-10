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
from typing import Union

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_access.permissions import any_user, system_process
from invenio_app.factory import create_api as _create_api

from oarepo_runtime.datastreams import BaseTransformer, BaseWriter, StreamBatch
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


@pytest.fixture(scope="module")
def identity():
    """Simple identity to interact with the service."""
    i = Identity(1)
    i.provides.add(UserNeed(1))
    i.provides.add(any_user)
    i.provides.add(system_process)
    return i


@pytest.fixture()
def custom_fields():
    prepare_cf_indices()
