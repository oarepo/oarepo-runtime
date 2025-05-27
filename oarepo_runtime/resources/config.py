from invenio_rdm_records.resources.config import (
    RDMRecordResourceConfig,
)

class BaseRecordResourceConfig(RDMRecordResourceConfig):
    """Record resource configuration."""

    blueprint_name = None
    url_prefix = None

    routes = RDMRecordResourceConfig.routes
    routes["all-prefix"] = "/all"