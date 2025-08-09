# type: ignore  # noqa
"""Example service."""

from invenio_access.permissions import Identity
from invenio_drafts_resources.services import RecordServiceConfig
from invenio_drafts_resources.services.records.components import (
    DraftFilesComponent,
    DraftMediaFilesComponent,
)
from invenio_drafts_resources.services.records.config import (
    SearchDraftsOptions,
    is_draft,
    is_record,
)
from invenio_records.api import RecordBase
from invenio_records_resources.services import ConditionalLink
from invenio_records_resources.services import (
    FileServiceConfig as BaseFileServiceConfig,
)
from invenio_records_resources.services import RecordLink
from invenio_records_resources.services.records.config import SearchOptions
from invenio_records_resources.services.records.facets import TermsFacet

from oarepo_runtime.services.config.permissions import EveryonePermissionPolicy
from oarepo_runtime.services.records.links import pagination_links_html
from oarepo_runtime.services.results import RecordItem, RecordList, ResultComponent

from .api import Draft, DraftMediaFiles, Record, RecordMediaFiles
from .schemas import RecordSchema


class SearchOptions(SearchOptions):
    """Search options for records."""

    facets = {
        "status": TermsFacet(
            field="status",
        )
    }


class SearchDraftsOptions(SearchDraftsOptions):
    """Search options for drafts."""

    facets = {
        "status": TermsFacet(
            field="status",
        )
    }


class TestResultComponent(ResultComponent):
    """Example result component for testing purposes."""

    def update_data(
        self, identity: Identity, record: RecordBase, projection: dict, expand: bool
    ) -> None:
        """Update the projection data with additional information."""
        projection["result_component"] = True


class ServiceConfig(RecordServiceConfig):
    """Mock service configuration."""

    permission_policy_cls = EveryonePermissionPolicy
    record_cls = Record
    draft_cls = Draft

    result_item_cls = type(
        "TestRecordItem", (RecordItem,), {"components": (TestResultComponent,)}
    )
    result_list_cls = type(
        "TestRecordList", (RecordList,), {"components": (TestResultComponent,)}
    )

    schema = RecordSchema
    search = SearchOptions
    search_drafts = SearchDraftsOptions

    components = RecordServiceConfig.components + [
        DraftFilesComponent,
        DraftMediaFilesComponent,
    ]

    links_search = {
        **RecordServiceConfig.links_search,
        **pagination_links_html("{+ui}/docs/{?args*}"),
    }

    links_item = {
        "self": ConditionalLink(
            cond=is_record,
            if_=RecordLink("{+api}/mocks/{id}"),
            else_=RecordLink("{+api}/mocks/{id}/draft"),
        ),
        "self_html": ConditionalLink(
            cond=is_record,
            if_=RecordLink("{+ui}/mocks/{id}"),
            else_=RecordLink("{+ui}/uploads/{id}"),
        ),
        "latest": RecordLink("{+api}/mocks/{id}/versions/latest"),
        "latest_html": RecordLink("{+ui}/mocks/{id}/latest"),
        "draft": RecordLink("{+api}/mocks/{id}/draft", when=is_record),
        "record": RecordLink("{+api}/mocks/{id}", when=is_draft),
        "publish": RecordLink("{+api}/mocks/{id}/draft/actions/publish", when=is_draft),
        "versions": RecordLink("{+api}/mocks/{id}/versions"),
    }


class MediaFilesRecordServiceConfig(RecordServiceConfig):
    """Record with media files service config."""

    service_id = "mock-record-media-files-service"
    record_cls = RecordMediaFiles
    draft_cls = DraftMediaFiles

    components = [
        DraftMediaFilesComponent,
    ]


class FileServiceConfig(BaseFileServiceConfig):
    """File service configuration."""

    allow_upload = False
    permission_policy_cls = EveryonePermissionPolicy
    record_cls = Record


class DraftFileServiceConfig(BaseFileServiceConfig):
    """File service configuration."""

    permission_policy_cls = EveryonePermissionPolicy
    permission_action_prefix = "draft_"
    record_cls = Draft


class MediaFileServiceConfig(BaseFileServiceConfig):
    """File service configuration."""

    service_id = "record-media-files-service"
    allow_upload = False
    permission_policy_cls = EveryonePermissionPolicy
    permission_action_prefix = "draft_media_"
    record_cls = RecordMediaFiles


class DraftMediaFileServiceConfig(BaseFileServiceConfig):
    """File service configuration."""

    service_id = "draft-media-files"
    permission_policy_cls = EveryonePermissionPolicy
    permission_action_prefix = "draft_media_"
    record_cls = DraftMediaFiles
