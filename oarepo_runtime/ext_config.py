from oarepo_runtime.config.permissions_presets import (
    AuthenticatedPermissionPolicy,
    EveryonePermissionPolicy,
    OaiHarvesterPermissionPolicy,
    ReadOnlyPermissionPolicy,
)
from oarepo_runtime.datastreams.fixtures import default_config_generator
from oarepo_runtime.datastreams.readers.excel import ExcelReader
from oarepo_runtime.datastreams.readers.json import JSONLinesReader, JSONReader
from oarepo_runtime.datastreams.readers.service import ServiceReader
from oarepo_runtime.datastreams.readers.yaml import YamlReader
from oarepo_runtime.datastreams.writers.service import ServiceWriter
from oarepo_runtime.datastreams.writers.yaml import YamlWriter

OAREPO_PERMISSIONS_PRESETS = {
    "read_only": ReadOnlyPermissionPolicy,
    "everyone": EveryonePermissionPolicy,
    "oai_harvester": OaiHarvesterPermissionPolicy,
    "authenticated": AuthenticatedPermissionPolicy,
}


DEFAULT_DATASTREAMS_READERS = {
    "excel": ExcelReader,
    "yaml": YamlReader,
    "json": JSONReader,
    "json-lines": JSONLinesReader,
    "service": ServiceReader,
}

DEFAULT_DATASTREAMS_READERS_BY_EXTENSION = {
    "xlsx": "excel",
    "yaml": "yaml",
    "yml": "yaml",
    "json": "json",
    "json5": "json",
    "jsonl": "json-lines",
}

DEFAULT_DATASTREAMS_WRITERS = {"service": ServiceWriter, "yaml": YamlWriter}

DEFAULT_DATASTREAMS_TRANSFORMERS = {}


DATASTREAMS_READERS = {}

DATASTREAMS_READERS_BY_EXTENSION = {}

DATASTREAMS_WRITERS = {}

DATASTREAMS_TRANSFORMERS = {}

DEFAULT_DATASTREAMS_EXCLUDES = []

DATASTREAMS_CONFIG_GENERATOR = default_config_generator
