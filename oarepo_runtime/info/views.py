import importlib
import json
import logging
import os
import re
from functools import cached_property
from typing import Literal
from urllib.parse import urljoin, urlparse, urlunparse

import importlib_metadata
import importlib_resources
import marshmallow as ma
from flask import current_app, request, url_for
from flask.ctx import RequestContext
from flask.globals import _cv_request
from flask_resources import (
    Resource,
    ResourceConfig,
    from_conf,
    request_parser,
    resource_requestctx,
    response_handler,
    route,
)
from flask_restful import abort
from invenio_base.utils import obj_or_import_string
from invenio_jsonschemas import current_jsonschemas
from invenio_records_resources.proxies import (
    current_service_registry,
    current_transfer_registry,
)

from oarepo_runtime.proxies import current_runtime

logger = logging.getLogger("oarepo_runtime.info")


class InfoConfig(ResourceConfig):
    blueprint_name = "oarepo_runtime_info"
    url_prefix = "/.well-known/repository"

    schema_view_args = {"schema": ma.fields.Str()}
    model_view_args = {"model": ma.fields.Str()}

    def __init__(self, app):
        self.app = app

    @cached_property
    def components(self):
        return tuple(
            obj_or_import_string(x)
            for x in self.app.config.get("INFO_ENDPOINT_COMPONENTS", [])
        )

schema_view_args = request_parser(from_conf("schema_view_args"), location="view_args")
model_view_args = request_parser(from_conf("model_view_args"), location="view_args")


class InfoResource(Resource):
    pass