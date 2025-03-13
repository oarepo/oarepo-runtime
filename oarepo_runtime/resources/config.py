import marshmallow as ma
from flask_resources import (
    JSONDeserializer,
    RequestBodyParser,
)
from invenio_drafts_resources.resources import RecordResourceConfig
from invenio_rdm_records.resources.args import RDMSearchRequestArgsSchema
from invenio_rdm_records.resources.config import RDMRecordResourceConfig
from invenio_records_resources.services.base.config import FromConfig


class BaseRecordResourceConfig(RDMRecordResourceConfig):
    """Record resource configuration."""

    blueprint_name = None
    url_prefix = None

    routes = RecordResourceConfig.routes

    routes["delete-record"] = "/<pid_value>/delete"
    routes["restore-record"] = "/<pid_value>/restore"
    routes["set-record-quota"] = "/<pid_value>/quota"
    routes["set-user-quota"] = "/users/<pid_value>/quota"
    routes["item-revision-list"] = "/<pid_value>/revisions"
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
        # 'application/ld+json;profile="https://w3id.org/ro/crate/1.1"': RequestBodyParser(
        #     ROCrateJSONDeserializer()
        # ),
    }

    request_search_args = FromConfig(
        "RDM_SEARCH_ARGS_SCHEMA", default=RDMSearchRequestArgsSchema
    )
