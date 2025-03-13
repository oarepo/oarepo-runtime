import marshmallow as ma
from flask_resources import (
    JSONDeserializer,
    JSONSerializer,
    RequestBodyParser,
    ResponseHandler,
)
from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_rdm_records.resources.args import RDMSearchRequestArgsSchema
from invenio_rdm_records.resources.config import (
    RDMRecordResourceConfig,
)
from invenio_records_resources.resources.records.headers import etag_headers

record_serializers = {
    "application/json": ResponseHandler(JSONSerializer(), headers=etag_headers),
}


class BaseRecordResourceConfig(RDMRecordResourceConfig):
    """Record resource configuration."""

    blueprint_name = None
    url_prefix = None

    routes = RecordResourceConfig.routes

    routes["delete-record"] = "/<pid_value>/delete"
    routes["restore-record"] = "/<pid_value>/restore"
    routes["set-record-quota"] = "/<pid_value>/quota"
    routes["set-user-quota"] = "/users/<pid_value>/quota"
    routes["all-prefix"] = "/all"

    request_view_args = {
        "pid_value": ma.fields.Str(),
    }

    request_read_args = {
        "style": ma.fields.Str(),
        "locale": ma.fields.Str(),
        "include_deleted": ma.fields.Bool(),
    }

    request_body_parsers = {
        "application/json": RequestBodyParser(JSONDeserializer()),
    }

    request_search_args = RDMSearchRequestArgsSchema

    response_handlers = record_serializers
