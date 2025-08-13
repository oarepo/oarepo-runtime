#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Runtime API classes that are returned from the current_runtime instance."""

from __future__ import annotations

import dataclasses
from functools import cached_property
from typing import TYPE_CHECKING, Any, cast

from flask import current_app
from invenio_base import invenio_url_for
from invenio_base.utils import obj_or_import_string
from invenio_records_resources.proxies import current_service_registry

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from flask_resources.responses import ResponseHandler
    from flask_resources.serializers import BaseSerializer
    from invenio_drafts_resources.records.api import Draft
    from invenio_records_resources.records.api import RecordBase
    from invenio_records_resources.resources.records.config import RecordResourceConfig
    from invenio_records_resources.resources.records.resource import RecordResource
    from invenio_records_resources.services import RecordService, RecordServiceConfig


@dataclasses.dataclass
class Export:
    """Configuration of an export format.

    Exports are shown on the record landing page and user can download them.
    """

    code: str
    """Code of the export format, used to identify the export format in the URL."""

    name: LazyString
    """Name of the export format, human readable."""

    mimetype: str
    """MIME type of the export format."""

    serializer: BaseSerializer
    """Serializer used to serialize the record into the export format."""

    display: bool = True
    """Whether the export format is displayed in the UI."""

    oai_metadata_prefix: str | None = None
    """OAI metadata prefix, if applicable. If not set, the export can not be used in OAI-PMH responses."""

    oai_schema: str | None = None
    """OAI schema, if applicable. If not set, the export can not be used in OAI-PMH responses."""

    oai_namespace: str | None = None
    """OAI namespace, if applicable. If not set, the export can not be used in OAI-PMH responses."""


class Model[
    S: RecordService = RecordService,
    C: RecordServiceConfig = RecordServiceConfig,
    R: RecordBase = RecordBase,
    D: Draft = Draft,
    # not sure why this is flagged by pyright as an error
    RR: RecordResource = RecordResource,  # pyright: ignore[reportGeneralTypeIssues]
    RC: RecordResourceConfig = RecordResourceConfig,
]:
    """Model configuration.

    Every model in oarepo repository must have this configuration which must be
    registered in the `oarepo.runtime` extension via the OAREPO_MODELS config
    variable.
    """

    code: str
    """Code of the model, used to identify the model"""

    name: str | LazyString
    """Name of the model, human readable."""

    version: str
    """Version of the model, should be a valid semantic version."""

    description: str | LazyString | None = None
    """Description of the model, human readable."""

    records_alias_enabled: bool = False
    """Whether the records alias is enabled for this model. Such models will be searchable
    via the `/api/records` endpoint."""

    def __init__(  # noqa: PLR0913 more attributes as we are creating a config
        self,
        *,
        code: str,
        name: str | LazyString,
        version: str,
        service: str | S,
        resource_config: RC | str,
        # params with default values
        service_config: C | None = None,
        description: str | LazyString | None = None,
        record: type[R] | None = None,
        draft: type[D] | None = None,
        resource: str | RR = "invenio_records_resources.resources.records.resource.RecordResource",
        exports: list[Export] | None = None,
        records_alias_enabled: bool = True,
    ):
        """Initialize the model configuration.

        :param name: Name of the model, human readable.
        :param version: Version of the model, should be a valid semantic version.
        :param description: Description of the model, human readable.
        :param service: Name of the service inside the `current_service_registry` or
            a configured service instance.
        :param service_config: Service configuration, if not provided,
            if will be taken from the service.
        :param record: Record class, if not provided, it will be taken from the service
            configuration.
        :param draft: Draft class, if not provided, it will be taken from the service
            configuration.
        :param resource: Resource class or string import path to the resource class.
            If not provided, it will be taken from the service configuration.
        :param resource_config: Resource configuration, if not provided, it will be
            taken from the resource class.
        :param exports: List of export formats that can be used to export the record.
            If not provided, no exports are available.
        :param records_alias_enabled: Whether the records alias is enabled for this model.
            Such models will be searchable via the `/api/records` endpoint.
        """
        self.code = code
        self.name = name
        self.version = version
        self.description = description
        self.records_alias_enabled = records_alias_enabled

        # lazy getters ...
        self._record = record
        self._draft = draft
        self._service = service
        self._service_config = service_config
        self._resource = resource
        self._resource_config = resource_config
        self._exports = exports or []

    @property
    def service(self) -> S:
        """Get the service."""
        if isinstance(self._service, str):
            return cast(
                "S",
                current_service_registry.get(self._service),  # type: ignore[attr-defined]
            )
        return self._service

    @property
    def service_config(self) -> C:
        """Get the service configuration."""
        if self._service_config is not None:
            return self._service_config
        return cast("C", self.service.config)

    @property
    def record_cls(self) -> type[R]:
        """Get the record class."""
        if self._record is None:
            return cast("type[R]", self.service.config.record_cls)
        return self._record

    @property
    def draft_cls(self) -> type[D] | None:
        """Get the draft class."""
        if self._draft is None:
            if hasattr(self.service.config, "draft_cls"):
                return cast("type[D]", self.service.config.draft_cls)
            return None
        return self._draft

    @property
    def api_blueprint_name(self) -> str:
        """Get the API blueprint name for the model."""
        return cast("str", self.resource_config.blueprint_name)

    def api_url(self, view_name: str, **kwargs: Any) -> str:
        """Get the API URL for the model."""
        return cast("str", invenio_url_for(f"{self.api_blueprint_name}.{view_name}", **kwargs))

    @cached_property
    def resource_config(self) -> RC:
        """Get the resource configuration."""
        if isinstance(self._resource_config, str):
            resource_config_class: type[RC] = cast("type[RC]", obj_or_import_string(self._resource_config))
            # need to import it here to avoid circular import issues
            from .config import build_config

            return build_config(resource_config_class, current_app)
        return self._resource_config

    @cached_property
    def resource(self) -> RR:
        """Get the resource."""
        if isinstance(self._resource, str):
            resource_class = obj_or_import_string(self._resource)
            if resource_class is None:
                raise ValueError(f"Resource class {self._resource} can not be None.")
            return cast(
                "RR",
                resource_class(
                    service=self.service,
                    config=self.resource_config,
                ),
            )
        return self._resource

    @property
    def exports(self) -> list[Export]:
        """Get all exportable response handlers."""
        return self._exports

    @property
    def response_handlers(self) -> dict[str, ResponseHandler]:
        """Get all response handlers from the resource configuration."""
        return cast("dict[str, ResponseHandler]", self.resource_config.response_handlers)
