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
    def create_url_rules(self):
        return [
            route("GET", "/", self.repository),
            route("GET", "/models", self.models),
            route("GET", "/schema/<path:schema>", self.schema),
            route("GET", "/models/<model>", self.model),
        ]

    def call_components(self, method_name, **kwargs):
        for component in self.components:
            if hasattr(component, method_name):
                getattr(component, method_name)(**kwargs)

    @cached_property
    def components(self):
        return [x(self) for x in self.config.components]

    @response_handler(many=True)
    def models(self):
        return current_runtime.models, 200

    @schema_view_args
    @response_handler()
    def schema(self):
        schema = resource_requestctx.view_args["schema"]
        return current_jsonschemas.get_schema(schema, resolved=True), 200


    @model_view_args
    @response_handler()
    def model(self):
        model = resource_requestctx.view_args["model"]
        for _model in importlib_metadata.entry_points().select(
            group="oarepo.models", name=model
        ):
            package_name, file_name = _model.value.split(":")
            model_data = json.loads(
                importlib_resources.files(package_name).joinpath(file_name).read_text()
            )
            return self._remove_implementation_details_from_model(model_data), 200
        abort(404)

    IMPLEMENTATION_DETAILS = re.compile(
        r"""
^(
  class | 
  .*-class |
  base-classes |
  .*-base-classes |
  module |
  generate |
  imports |
  extra-code |
  components |
  .*-args
)$
    """,
        re.VERBOSE,
        )

    def _remove_implementation_details_from_model(self, model):
        if isinstance(model, dict):
            return self._remove_implementation_details_from_model_dict(model)
        elif isinstance(model, list):
            return self._remove_implementation_details_from_model_list(model)
        else:
            return model

    def _remove_implementation_details_from_model_dict(self, model):
        ret = {}
        for k, v in model.items():
            if not self.IMPLEMENTATION_DETAILS.match(k):
                new_value = self._remove_implementation_details_from_model(v)
                if new_value is not None and new_value != {} and new_value != []:
                    ret[k] = new_value
        return ret

    def _remove_implementation_details_from_model_list(self, model):
        ret = []
        for v in model:
            new_value = self._remove_implementation_details_from_model(v)
            if new_value is not None and new_value != {} and new_value != []:
                ret.append(new_value)
        return ret

    def _get_resource_config_class(self, model_data):
        model_class = model_data["resource-config"]["class"]
        return obj_or_import_string(model_class)()

    def _get_model_content_types(self, service, model):
        """Get the content types supported by the model. Returns a list of:

        content_type="application/json",
        name="Invenio RDM JSON",
        description="Invenio RDM JSON as described in",
        schema=url / "schemas" / "records" / "record-v6.0.0.json",
        can_export=True,
        can_deposit=True,
        """

        content_types = []
        # implicit content type
        content_types.append(
            {
                "content_type": "application/json",
                "name": f"Internal json serialization of {model['model-name']}",
                "description": "This content type is serving this model's native format as described on model link.",
                "schema": url_for(
                    "oarepo_runtime_info.schema",
                    schema=model.record_json_schema,
                    _external=True,
                ),
                "can_export": True,
                "can_deposit": True,
            }
        )

        # export content types
        try:
            for accept_type, handler in model.resource_config.response_handlers.items():
                if accept_type == "application/json":
                    continue
                curr_item = {
                    "content_type": accept_type,
                    "name": getattr(handler, "name", accept_type),
                    "description": getattr(handler, "description", ""),
                    "can_export": True,
                    "can_deposit": False,
                }
                if handler.serializer is not None:
                    if hasattr(handler.serializer, "name"):
                        curr_item["name"] = handler.serializer.name
                    if hasattr(handler.serializer, "description"):
                        curr_item["description"] = handler.serializer.description
                    if hasattr(handler.serializer, "info"):
                        curr_item.update(handler.serializer.info(service))
                content_types.append(curr_item)
        except:  # NOSONAR noqa
            logger.exception("Failed to get model schemas")
        return content_types

    def _get_service(self, model_data):
        service_id = model_data["service-config"]["service-id"]
        try:
            service = current_service_registry.get(service_id)
        except KeyError:
            return None
        return service

    def _get_service_class(self, model_data):
        service_id = model_data["service"]["class"]
        return obj_or_import_string(service_id)

    def _get_model_features(self, model):
        features = []
        if model.get("requests", {}):
            features.append("requests")
        if model.get("draft", {}):
            features.append("drafts")
        if model.get("files", {}):
            features.append("files")
        return features

    def _get_model_html_endpoint(self, model):
        try:
            return urljoin(
                self._get_model_api_endpoint(model),
                model["resource-config"]["base-html-url"],
            )
        except:  # NOSONAR noqa
            logger.exception("Failed to get model html endpoint")
            return None

    def _get_model_model_endpoint(self, model):
        try:
            return url_for("oarepo_runtime_info.model", model=model, _external=True)
        except:  # NOSONAR noqa
            logger.exception("Failed to get model model endpoint")
            return None

    def _get_model_api_endpoint(self, model):
        try:
            alias = model["api-blueprint"]["alias"]
            return api_url_for(f"{alias}.search", _external=True)
        except:  # NOSONAR noqa
            logger.exception("Failed to get model api endpoint")
            return None

    def _get_model_draft_endpoint(self, model):
        try:
            alias = model["api-blueprint"]["alias"]
            return api_url_for(f"{alias}.search_user_records", _external=True)
        except:  # NOSONAR noqa
            logger.exception("Failed to get model draft endpoint")
            return None

    @cached_property
    def model_data(self):
        data = []
        # iterate entrypoint oarepo.models
        # TODO: kontrola, brat modely odsud?
        # for model in importlib_metadata.entry_points().select(group="oarepo.models"):
        for model in current_runtime.models.values():

            # TODO: v rdm-12 vznika v ramci ./run-tests.sh; odkudbrat odjinud pro rdm-13?
            # package_name, file_name = model.value.split(":")
            # model_data = json.loads(
            #     importlib_resources.files(package_name).joinpath(file_name).read_text()
            # )
            # model_data = model_data.get("model", {})
            # if model_data.get("type") != "model":
            #     continue
            model_data = {}

            resource_config = model.resource.config
            resource_config_class = model.resource_config.__class__

            service = model.service

            # service_class = self._get_service_class(model_data)
            service_class = model.service.__class__

            if not service or type(service) != service_class:
                continue

            # check if the service class is inside OAREPO_GLOBAL_SEARCH and if not, skip it
            global_search_models = current_app.config.get("GLOBAL_SEARCH_MODELS", [])
            # for global_model in global_search_models:
            #     if global_model["model_service"] == service_class:
            #         break
            # else:
            #     continue

            model_features = self._get_model_features(model_data)

            links = {
                "html": self._get_model_html_endpoint(model_data),
                "model": self._get_model_model_endpoint(model.name),
                # "openapi": url_for(self._get_model_openapi_endpoint(model_data), _external=True)
            }

            links["records"] = self._get_model_api_endpoint(model_data)
            if "drafts" in model_features:
                links["drafts"] = self._get_model_draft_endpoint(model_data)
            links["deposit"] = links["records"]

            data.append(
                {
                    "schema": model.record_json_schema,
                    "type": model.record_json_schema,
                    "name": model.name,
                    "description": model.description,
                    "version": model.version,
                    "features": None,
                    "links": links,
                    "content_types": None,
                    "metadata": None

                    # TODO
                    # "features": model_features,
                    # "links": links,
                    # # TODO: we also need to get previous schema versions here if we support
                    # #   multiple version of the same schema at the same time
                    # "content_types": self._get_model_content_types(
                    #     service, resource.config, model_data
                    # ),
                    # "metadata": model_data.get("properties", {}).get("metadata", None)
                    #             is not None,
                }
            )
        self.call_components("model", data=data)
        data.sort(key=lambda x: x["type"])
        return data

    @response_handler()
    def repository(self):
        """Repository endpoint."""
        links = {
            "self": url_for(request.endpoint, _external=True),
            "api": replace_path_in_url(
                url_for(request.endpoint, _external=True), "/api"
            ),
            "models": url_for("oarepo_runtime_info.models", _external=True),
        }
        try:
            import invenio_requests  # noqa

            links["requests"] = api_url_for("requests.search", _external=True)
        except ImportError:
            pass

        ret = {
            "schema": "local://introspection-v1.0.0",
            "name": current_app.config.get("THEME_SITENAME", ""),
            "description": current_app.config.get("REPOSITORY_DESCRIPTION", ""),
            "version": os.environ.get("DEPLOYMENT_VERSION", "local development"),
            "invenio_version": get_package_version("oarepo"),
            "transfers": list(current_transfer_registry.get_transfer_types()),
            "links": links,
            "features": [
                *_add_feature_if_can_import("drafts", "invenio_drafts_resources"),
                *_add_feature_if_can_import("workflows", "oarepo_workflows"),
                *_add_feature_if_can_import("requests", "invenio_requests"),
                *_add_feature_if_can_import("communities", "invenio_communities"),
                *_add_feature_if_can_import("request_types", "oarepo_requests"),
            ],
        }
        if len(self.model_data) == 1:
            ret["default_model"] = self.model_data[0]["name"]

        self.call_components("repository", data=ret)
        return ret, 200

def create_wellknown_blueprint(app) -> Resource:
    """Create an info blueprint."""
    config_class = obj_or_import_string(
        app.config.get("INFO_ENDPOINT_CONFIG", InfoConfig)
    )
    return InfoResource(config=config_class(app)).as_blueprint()


def get_package_version(package_name: str) -> str | None:
    """Get package version."""
    from pkg_resources import get_distribution

    try:
        return re.sub(r"\+.*", "", get_distribution(package_name).version)
    except Exception:  # NOSONAR noqa
        logger.exception(f"Failed to get package version for {package_name}")
        return None


def api_url_for(endpoint, _external=True, **values):
    """API url_for."""
    try:
        api_app = current_app.wsgi_app.mounts["/api"]
    except:
        api_app = current_app

    site_api_url = current_app.config["SITE_API_URL"]
    site_url = current_app.config["SITE_UI_URL"]
    current_request_context = _cv_request.get()
    try:
        new_context = RequestContext(app=api_app, environ=request.environ)
        _cv_request.set(new_context)
        base_url = api_app.url_for(endpoint, **values, _external=_external)
        if base_url.startswith(site_api_url):
            return base_url
        if base_url.startswith(site_url):
            return base_url.replace(site_url, site_api_url)
        raise ValueError(
            f"URL {base_url} does not start with {site_url} or {site_api_url}"
        )
    finally:
        _cv_request.set(current_request_context)


def replace_path_in_url(url, path) -> Literal[b""]:
    # Parse the URL into its components
    parsed_url = urlparse(url)

    # Replace the path with '/api'
    new_parsed_url = parsed_url._replace(path=path)

    # Reconstruct the URL with the new path
    new_url = urlunparse(new_parsed_url)

    return new_url


def _add_feature_if_can_import(feature, module) -> list[str]:
    try:
        importlib.import_module(module)
        return [feature]
    except ImportError:
        return []


def to_current_language(data):
    if isinstance(data, dict):
        from flask_babel import get_locale

        return data.get(get_locale().language)
    return data
