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
    from collections.abc import Mapping

    from flask_babel.speaklater import LazyString
    from flask_resources.responses import ResponseHandler
    from flask_resources.serializers import BaseSerializer
    from invenio_drafts_resources.records.api import Draft
    from invenio_records.systemfields import ConstantField
    from invenio_records_resources.records.api import Record
    from invenio_records_resources.records.systemfields.pid import (
        ModelPIDField,
        ModelPIDFieldContext,
    )
    from invenio_records_resources.resources.records.config import RecordResourceConfig
    from invenio_records_resources.resources.records.resource import RecordResource
    from invenio_records_resources.services import (
        FileService,
        RecordService,
        RecordServiceConfig,
    )


@dataclasses.dataclass
class ModelMetadata:
    """Model metadata configuration.

    ModeMetadata is used in oarepo-model to add metadata to the model's oarepo_model_arguments dict.
    """

    types: dict[str, Any]
    """Dictionary of types passed from InvenioModelBuilder.type_registry"""
    metadata_type: str | None = None
    """Metadata type"""
    record_type: str | None = None
    """Record type"""


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
    R: Record = Record,
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

    def __init__(  # noqa: PLR0913 more attributes as we are creating a config
        self,
        *,
        code: str,
        name: str | LazyString,
        version: str,
        service: str | S,
        resource_config: RC | str,
        ui_model: Mapping[str, Any] | None = None,
        # params with default values
        service_config: C | None = None,
        description: str | LazyString | None = None,
        record: type[R] | None = None,
        draft: type[D] | None = None,
        resource: (str | RR) = "invenio_records_resources.resources.records.resource.RecordResource",
        file_service: FileService | None = None,
        draft_file_service: FileService | None = None,
        media_file_service: FileService | None = None,
        media_draft_file_service: FileService | None = None,
        exports: list[Export] | None = None,
        records_alias_enabled: bool = True,
        model_metadata: ModelMetadata | None = None,
        features: Mapping[str, Any] | None = None,
    ):
        """Initialize the model configuration.

        :param name: Name of the model, human-readable.
        :param version: Version of the model should be a valid semantic version.
        :param description: Description of the model, human-readable.
        :param service: Name of the service inside the `current_service_registry` or
            a configured service instance.
        :param service_config: Service configuration, if not provided,
            it will be taken from the service.
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
        :param records_alias_enabled: Whether the record alias is enabled for this model.
            Such models will be searchable via the `/api/records` endpoint.
        :param model_metadata: Metadata of the model.
        :param features: Features of the model. Filled by the feature presets themselves during registration.
        """
        self._code = code
        self._name = name
        self._version = version
        self._description = description
        self._records_alias_enabled = records_alias_enabled
        self._ui_model = ui_model or {}

        self._file_service = file_service
        self._draft_file_service = draft_file_service
        self._media_file_service = media_file_service
        self._media_draft_file_service = media_draft_file_service

        # lazy getters ...
        self._record = record
        self._draft = draft
        self._service = service
        self._service_config = service_config
        self._resource = resource
        self._resource_config = resource_config
        self._exports = exports or []
        self._model_metadata = model_metadata
        self._features = features

    @property
    def code(self) -> str:
        """Return the machine-understandable code of the model."""
        return self._code

    @property
    def name(self) -> str | LazyString:
        """Get the human-readable name of the model."""
        return self._name

    @property
    def version(self) -> str:
        """Get the model's version."""
        return self._version

    @property
    def description(self) -> str | LazyString | None:
        """Get the model's description."""
        return self._description

    @property
    def records_alias_enabled(self) -> bool:
        """Get the records alias enabled flag.

        This switch determines whether the records alias (/api/records)
        is enabled for this model and whether the model is indexed in global search.
        """
        return self._records_alias_enabled

    @property
    def model_metadata(self) -> ModelMetadata | None:
        """Get the model metadata."""
        return self._model_metadata

    @property
    def ui_model(self) -> Mapping[str, Any]:
        """Get the UI model."""
        return self._ui_model

    @property
    def service(self) -> S:
        """Get the service."""
        if isinstance(self._service, str):
            return cast(
                "S",
                current_service_registry.get(self._service),
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
            draft_cls = getattr(self.service.config, "draft_cls", None)
            if draft_cls:
                return cast("type[D]", draft_cls)
            return None
        return self._draft

    @property
    def file_service(self) -> FileService | None:
        """Get the file service."""
        return self._file_service

    @property
    def draft_file_service(self) -> FileService | None:
        """Get the draft file service."""
        return self._draft_file_service

    @property
    def media_file_service(self) -> FileService | None:
        """Get the media file service."""
        return self._media_file_service

    @property
    def media_draft_file_service(self) -> FileService | None:
        """Get the media draft file service."""
        return self._media_draft_file_service

    @property
    def api_blueprint_name(self) -> str:
        """Get the API blueprint name for the model."""
        return cast("str", self.resource_config.blueprint_name)

    @property
    def record_pid_type(self) -> str | None:
        """Get the PID type for the model."""
        return self._pid_type_from_record(self.record_cls)

    @property
    def record_json_schema(self) -> str:
        """Get the json schema of the record."""
        schema: ConstantField[Record, str] | None = getattr(self.record_cls, "schema", None)
        if schema is None:
            raise KeyError(f"Record class {self.record_cls} does not have a schema field.")  # pragma: no cover
        return schema.value  # type: ignore[no-any-return]

    @property
    def draft_pid_type(self) -> str | None:
        """Get the PID type for the model."""
        return self._pid_type_from_record(self.draft_cls)

    def _pid_type_from_record(self, record_cls: type[Record] | None) -> str | None:
        """Get the PID type from a record class, returning None if not found."""
        if record_cls is None:
            return None
        pid_context: ModelPIDFieldContext | None = getattr(record_cls, "pid", None)
        if pid_context is None:
            # registered record has no pid field
            return None  # pragma: no cover
        pid_field: ModelPIDField | None = getattr(pid_context, "field", None)
        if pid_field is None:
            # there is no pid field in the context
            return None  # pragma: no cover
        pid_provider = getattr(pid_field, "_provider", None)
        if not pid_provider:
            # there is no pid provider in the field
            return None  # pragma: no cover
        return getattr(pid_provider, "pid_type", None)

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

    @property
    def features(self) -> Mapping[str, Any] | None:
        """Get a mapping of features."""
        return self._features
