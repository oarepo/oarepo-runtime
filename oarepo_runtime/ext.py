#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Extension preset for runtime module."""

from __future__ import annotations

from functools import cached_property
from typing import TYPE_CHECKING, Any, cast

from flask import current_app
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.records.api import RecordBase

from . import config

if TYPE_CHECKING:  # pragma: no cover
    from flask import Flask
    from invenio_records_resources.services.records import RecordService, Service

    from .api import Model


class OARepoRuntime:
    """OARepo base of invenio oarepo client."""

    def __init__(self, app: Flask | None = None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        self.app = app
        self.init_config(app)
        app.extensions["oarepo-runtime"] = self

    def init_config(self, app: Flask) -> None:
        """Initialize the configuration for the extension."""
        app.config.setdefault("OAREPO_MODELS", {})
        for k, v in config.OAREPO_MODELS.items():
            if k not in app.config["OAREPO_MODELS"]:
                app.config["OAREPO_MODELS"][k] = v

    @property
    def models(self) -> dict[str, Model]:
        """Return the models registered in the extension."""
        return cast("dict[str, Model]", current_app.config["OAREPO_MODELS"])

    @cached_property
    def models_by_record_class(self) -> dict[type[RecordBase], Model]:
        """Return a mapping of record classes to their models."""
        ret = {
            model.record_cls: model
            for model in self.models.values()
            if model.record_cls is not None
        }
        ret.update(
            {
                model.draft_cls: model
                for model in self.models.values()
                if model.draft_cls is not None
            }
        )
        return ret

    @property
    def services(self) -> dict[str, Service]:
        """Return the services registered in the extension."""
        _services = current_service_registry._services  # type: ignore[attr-defined]  # noqa: SLF001
        return cast("dict[str, Service]", _services)

    def get_record_service_for_record(self, record: Any) -> RecordService:
        """Retrieve the associated service for a given record."""
        if not record:
            raise ValueError("Need to pass a record instance, got None")
        return self.get_record_service_for_record_class(type(record))

    def get_record_service_for_record_class(
        self, record_cls: type[RecordBase]
    ) -> RecordService:
        """Retrieve the service associated with a given record class."""
        for t in record_cls.mro():
            if t is RecordBase:
                break
            if t in self.models_by_record_class:
                model = self.models_by_record_class[t]
                return model.service
        raise KeyError(f"No service found for record class '{record_cls.__name__}'.")
