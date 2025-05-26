from flask_resources import (
    JSONSerializer,
    ResponseHandler,
)
from invenio_rdm_records.resources.config import (
    RDMRecordResourceConfig,
)
from invenio_records_resources.resources.records.headers import etag_headers

class BaseRecordResourceConfig(RDMRecordResourceConfig):
    """Record resource configuration."""

    blueprint_name = None
    url_prefix = None

    routes = RDMRecordResourceConfig.routes
    routes["all-prefix"] = "/all"

    """
    request_body_parsers = {
        "application/json": RequestBodyParser(JSONDeserializer()),
    }
    """

    """
    response_handlers = record_serializers
    """