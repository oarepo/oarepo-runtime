from invenio_records_resources.services import RecordLink
from invenio_records_resources.services import RecordServiceConfig
from invenio_records_resources.services import (
    RecordServiceConfig as InvenioRecordServiceConfig,
)
from invenio_records_resources.services import pagination_links

from records2.records.api import Records2Record
from records2.services.records.permissions import Records2PermissionPolicy
from records2.services.records.schema import Records2Schema
from records2.services.records.search import Records2SearchOptions


class Records2ServiceConfig(RecordServiceConfig):
    """Records2Record service config."""

    url_prefix = "/records2/"

    permission_policy_cls = Records2PermissionPolicy

    schema = Records2Schema

    search = Records2SearchOptions

    record_cls = Records2Record
    # todo should i leave this here?
    service_id = "records2"

    components = [*RecordServiceConfig.components]

    model = "records2"

    @property
    def links_item(self):
        return {
            "self": RecordLink("{self.url_prefix}{id}"),
        }

    @property
    def links_search(self):
        return pagination_links("{self.url_prefix}{?args*}")
