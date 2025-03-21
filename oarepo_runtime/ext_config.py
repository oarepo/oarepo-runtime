from invenio_records_resources.services.custom_fields import BooleanCF

from oarepo_runtime.datastreams.fixtures import default_config_generator
from oarepo_runtime.datastreams.readers.excel import ExcelReader
from oarepo_runtime.datastreams.readers.json import JSONLinesReader, JSONReader
from oarepo_runtime.datastreams.readers.service import ServiceReader
from oarepo_runtime.datastreams.readers.yaml import YamlReader
from oarepo_runtime.datastreams.writers.attachments_file import AttachmentsFileWriter
from oarepo_runtime.datastreams.writers.attachments_service import (
    AttachmentsServiceWriter,
)
from oarepo_runtime.datastreams.writers.publish import PublishWriter
from oarepo_runtime.datastreams.writers.service import ServiceWriter
from oarepo_runtime.datastreams.writers.yaml import YamlWriter
from oarepo_runtime.records.entity_resolvers import UserResolver
from oarepo_runtime.services.config.permissions_presets import (
    AuthenticatedPermissionPolicy,
    EveryonePermissionPolicy,
    OaiHarvesterPermissionPolicy,
    ReadOnlyPermissionPolicy,
)
from oarepo_runtime.services.facets.facet_groups_names import facet_groups_names

OAREPO_PERMISSIONS_PRESETS = {
    "read_only": ReadOnlyPermissionPolicy,
    "everyone": EveryonePermissionPolicy,
    "oai_harvester": OaiHarvesterPermissionPolicy,
    "authenticated": AuthenticatedPermissionPolicy,
}


DATASTREAMS_READERS = {
    "excel": ExcelReader,
    "yaml": YamlReader,
    "json": JSONReader,
    "json-lines": JSONLinesReader,
    "service": ServiceReader,
}

DATASTREAMS_READERS_BY_EXTENSION = {
    "xlsx": "excel",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "json5": "json",
    "jsonl": "json-lines",
}

DATASTREAMS_WRITERS = {
    "service": ServiceWriter,
    "attachments_service": AttachmentsServiceWriter,
    "yaml": YamlWriter,
    "attachments_file": AttachmentsFileWriter,
    "publish": PublishWriter,
}

DATASTREAMS_TRANSFORMERS = {}

DATASTREAMS_CONFIG_GENERATOR = default_config_generator

HAS_DRAFT_CUSTOM_FIELD = [BooleanCF("has_draft")]

OAREPO_FACET_GROUP_NAME = facet_groups_names

OWNER_ENTITY_RESOLVERS = [
    UserResolver(),
]
