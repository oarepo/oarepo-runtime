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

from typing import TYPE_CHECKING, cast

from invenio_records_resources.proxies import current_service_registry

if TYPE_CHECKING:
    from flask_babel.speaklater import LazyString
    from invenio_drafts_resources.records.api import Draft
    from invenio_records_resources.records.api import RecordBase
    from invenio_records_resources.services import RecordService, RecordServiceConfig


class Model[
    S: RecordService = RecordService,
    C: RecordServiceConfig = RecordServiceConfig,
    R: RecordBase = RecordBase,
    D: Draft = Draft,
]:
    """Model configuration.

    Every model in oarepo repository must have this configuration which must be
    registered in the `oarepo.runtime` extension via the OAREPO_MODELS config
    variable.
    """

    name: str | LazyString
    version: str
    description: str | LazyString | None = None
    global_search_enabled: bool = False

    def __init__(  # noqa: PLR0913 more attributes as we are creating a config
        self,
        name: str | LazyString,
        version: str,
        service: str | S,
        # params with default values
        service_config: C | None = None,
        description: str | LazyString | None = None,
        record: type[R] | None = None,
        draft: type[D] | None = None,
        global_search_enabled: bool = True,
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
        """
        self.name = name
        self.version = version
        self.description = description
        self.global_search_enabled = global_search_enabled

        # lazy getters ...
        self._record = record
        self._draft = draft
        self._service = service
        self._service_config = service_config

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
