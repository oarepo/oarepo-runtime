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

import json
from pathlib import Path

import pytest
from flask import Blueprint
from flask_principal import Identity, Need, UserNeed
from flask_resources import JSONDeserializer
from flask_resources.serializers import BaseSerializer
from invenio_app.factory import create_api as _create_api
from invenio_records_resources.proxies import current_service_registry
from invenio_vocabularies.records.models import VocabularyType

from oarepo_runtime.api import Export, Import
from oarepo_runtime.info.views import InfoResource, create_wellknown_blueprint
from oarepo_runtime.services.records.mapping import update_all_records_mappings

pytest_plugins = ("celery.contrib.pytest",)


class TestInfoComponent:
    """Test info component."""

    def __init__(self, resource: InfoResource) -> None:
        """Create the component."""
        self.resource = resource

    def repository(self, data):
        """Repository info."""
        data["test_info"] = "test"


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
    app_config["SITE_API_URL"] = "https://127.0.0.1:5000/api"
    app_config["SERVER_NAME"] = "127.0.0.1:5000"
    app_config["PREFERRED_URL_SCHEME"] = "https"

    app_config["INFO_ENDPOINT_COMPONENTS"] = [
        TestInfoComponent,
    ]

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


class DummySerializer:
    """Minimal serializer stub used in tests."""

    def serialize_object(self, obj):  # pragma: no cover - not used here
        """Serialize a single object."""
        return f"obj:{obj}"

    def serialize_object_list(self, obj_list):  # pragma: no cover - not used here
        """Serialize a list of objects."""
        return f"list:{len(obj_list)}"


class DataciteSerializer(BaseSerializer):
    """Minimal datacite serializer stub used in tests."""

    def serialize_object(self, _obj):
        """Serialize a single object."""
        with (Path(__file__).parent / "data/datacite_export.json").open() as f:
            return json.load(f)


def _export(code: str, mimetype: str, serializer=DummySerializer) -> Export:
    return Export(
        code=code,
        name="Test",
        mimetype=mimetype,
        serializer=serializer(),
        description="Test description",
    )


def _import(code: str, mimetype: str) -> Import:
    return Import(
        code=code,
        name="Test",
        mimetype=mimetype,
        deserializer=JSONDeserializer(),
        description="Test description",
    )


@pytest.fixture
def lang_type(db):
    """Get a language vocabulary type."""
    v = VocabularyType.create(id="languages", pid_type="lng")
    db.session.commit()
    return v


@pytest.fixture
def vocab_records(app, db, search_clear):
    from invenio_access.permissions import system_identity
    from invenio_vocabularies.proxies import current_service as vocabulary_service

    try:
        vocab_type = vocabulary_service.create_type(system_identity, "test-vocab", "v-test")
        vocabulary_service.create(
            system_identity,
            {
                "type": vocab_type.id,
                "id": "a",
                "title": {"en": "Test A", "cs": "Test A CS"},
            },
        )
        vocabulary_service.create(
            system_identity,
            {
                "type": vocab_type.id,
                "id": "b",
                "title": {"en": "Test B", "cs": "Test B CS"},
            },
        )
        vocabulary_service.indexer.refresh()
    # not sure why the database is not rolled back
    except Exception:  # noqa: S110, BLE001
        pass


@pytest.fixture
def info_blueprint(app):
    app.register_blueprint(create_wellknown_blueprint(app))


@pytest.fixture(scope="module")
def app_with_mock_ui_bp(app):
    bp = Blueprint("mock", __name__)

    # mock UI resource
    @bp.route("/test-ui-links/preview/<pid_value>", methods=["GET"])
    def preview(pid_value: str) -> str:
        return "preview ok"

    @bp.route("/test-ui-links/", methods=["GET"])
    def search() -> str:
        return "search ok"

    @bp.route("/test-ui-links/uploads/<pid_value>", methods=["GET"])
    def deposit_edit(pid_value: str) -> str:
        return "deposit edit ok"

    @bp.route("/test-ui-links/uploads/new", methods=["GET"])
    def deposit_create() -> str:
        return "deposit create ok"

    @bp.route("/test-ui-links/records/<pid_value>")
    def record_detail(pid_value) -> str:
        return "detail ok"

    @bp.route("/test-ui-links/records/<pid_value>/latest", methods=["GET"])
    def record_latest(pid_value: str) -> str:
        return "latest ok"

    @bp.route("/test-ui-links/records/<pid_value>/export/<export_format>", methods=["GET"])
    def record_export(pid_value, export_format: str) -> str:
        return "export ok"

    app.register_blueprint(bp)
    return app
