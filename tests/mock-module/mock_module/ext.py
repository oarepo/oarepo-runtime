# type: ignore  # noqa
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Drafts-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
from __future__ import annotations

from functools import cached_property

from invenio_drafts_resources.services.records import RecordService
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.resources.records import RecordResource
from invenio_records_resources.services.files import FileService

from oarepo_runtime import Model
from tests.conftest import DataciteSerializer, DublinCoreSerializer, _export, _import

from .resource import RecordResourceConfig
from .service import (
    DraftFileServiceConfig,
    DraftMediaFileServiceConfig,
    FileServiceConfig,
    MediaFileServiceConfig,
    ServiceConfig,
)


class MockModuleExt:
    """Mock module extension for testing purposes."""

    def __init__(self, app):
        """Initialize the mock module extension."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the mock module."""
        self.app = app
        self.init_config(app)
        app.extensions["mock-module"] = self

    def init_config(self, app):
        """Initialize the configuration for the mock module."""
        app.config.setdefault("OAREPO_MODELS", {})["mock"] = Model(
            code="mock",
            name="mock",
            version="1.0.0",
            service="mock-record-service",
            records_alias_enabled=True,
            resource_config=self.resource_config,
            file_service=self.file_service,
            draft_file_service=self.draft_file_service,
            exports=[
                _export("mock-api", "application/json"),
                _export("datacite", "application/vnd.datacite.datacite+json", serializer=DataciteSerializer),
                _export("dublincore", "application/x-dc+xml", serializer=DublinCoreSerializer),
            ],
            imports=[_import("mock-api", "application/json")],
            features={
                "draft": {"enabled": True},
                "files": {"enabled": True},
                "requests": {"enabled": True},
            },
            ui_blueprint_name="mock",
        )

    @cached_property
    def file_service(self):
        """File service fixture."""
        return FileService(FileServiceConfig)

    @cached_property
    def draft_file_service(self):
        """File service fixture."""
        return FileService(DraftFileServiceConfig)

    @cached_property
    def media_file_service(self):
        """File service fixture."""
        return FileService(MediaFileServiceConfig)

    @cached_property
    def media_draft_file_service(self):
        """File service fixture."""
        return FileService(DraftMediaFileServiceConfig)

    @cached_property
    def service(self):
        """Record service fixture."""
        return RecordService(
            ServiceConfig,
            files_service=self.file_service,
            draft_files_service=self.draft_file_service,
        )

    @cached_property
    def resource_config(self):
        """Resource fixture."""
        return RecordResourceConfig()

    @cached_property
    def resource(self):
        """Resource fixture."""
        return RecordResource(self.resource_config, self.service)


def finalize_mock_module(app):
    """Finalize the mock module."""
    with app.app_context():
        # Register the mock module extension

        # Register services
        current_service_registry.register(
            app.extensions["mock-module"].service,
            service_id="mock-record-service",
        )
        current_service_registry.register(
            app.extensions["mock-module"].file_service,
            service_id="mock-record-file-service",
        )
        current_service_registry.register(
            app.extensions["mock-module"].draft_file_service,
            service_id="mock-record-draft-file-service",
        )
