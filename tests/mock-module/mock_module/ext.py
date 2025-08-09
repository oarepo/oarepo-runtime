# type: ignore  # noqa
from functools import cached_property

from invenio_drafts_resources.services.records import RecordService
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.files import FileService

from oarepo_runtime import Model

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
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Initialize the mock module."""
        self.app = app
        self.init_config(app)
        app.extensions["mock-module"] = self

    def init_config(self, app):
        app.config.setdefault("OAREPO_MODELS", {})["mock"] = Model(
            name="mock",
            version="1.0.0",
            service="mock-record-service",
            global_search_enabled=True,
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
        return RecordService(
            ServiceConfig,
            files_service=self.file_service,
            draft_files_service=self.draft_file_service,
        )


def finalize_mock_module(app):
    """Finalize the mock module."""
    with app.app_context():
        # Register the mock module extension

        # Register services
        current_service_registry.register(
            app.extensions["mock-module"].service,
            service_id="mock-record-service",
        )
