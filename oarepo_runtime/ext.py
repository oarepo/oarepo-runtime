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
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_pidstore.models import PersistentIdentifier
from invenio_records.api import Record as RecordBase
from invenio_records_resources.proxies import current_service_registry

from . import config

if TYPE_CHECKING:  # pragma: no cover
    from collections.abc import Iterable
    from uuid import UUID

    from flask import Flask
    from invenio_drafts_resources.records.api import Draft
    from invenio_records_resources.records.api import Record
    from invenio_records_resources.services.base.service import Service
    from invenio_records_resources.services.files.service import FileService
    from invenio_records_resources.services.records import RecordService

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

    @property
    def rdm_models(self) -> Iterable[Model]:
        """Return the RDM models registered in the extension."""
        return [v for v in self.models.values() if v.records_alias_enabled]

    @cached_property
    def models_by_record_class(self) -> dict[type[Record], Model]:
        """Return a mapping of record classes to their models."""
        ret = {model.record_cls: model for model in self.models.values() if model.record_cls is not None}
        ret.update({model.draft_cls: model for model in self.models.values() if model.draft_cls is not None})
        return ret

    @cached_property
    def record_class_by_pid_type(self) -> dict[str, type[Record]]:
        """Return a mapping of PID types to their record classes."""
        ret: dict[str, type[Record]] = {}
        for model in self.models.values():
            pid_type = model.record_pid_type
            if pid_type is not None:
                ret[pid_type] = model.record_cls
        return ret

    @cached_property
    def draft_class_by_pid_type(self) -> dict[str, type[Draft]]:
        """Return a mapping of PID types to their draft classes."""
        ret: dict[str, type[Draft]] = {}
        for model in self.models.values():
            pid_type = model.draft_pid_type
            if pid_type is not None and model.draft_cls is not None:
                ret[pid_type] = model.draft_cls
        return ret

    @cached_property
    def model_by_pid_type(self) -> dict[str, Model]:
        """Return a mapping of PID types to their models."""
        ret: dict[str, Model] = {}
        for model in self.models.values():
            pid_type = model.record_pid_type
            if pid_type is not None:
                ret[pid_type] = model
            pid_type = model.draft_pid_type
            if pid_type is not None:
                ret[pid_type] = model
        return ret

    @cached_property
    def models_by_schema(self) -> dict[str, Model]:
        """Return a mapping of schemas to their models."""
        ret: dict[str, Model] = {}
        for model in self.models.values():
            if model.record_cls is not None:
                ret[model.record_cls.schema.value] = model  # type: ignore  # noqa
        return ret

    @cached_property
    def rdm_models_by_schema(self) -> dict[str, Model]:
        """Return a mapping of RDM schemas to their models."""
        return {schema: model for schema, model in self.models_by_schema.items() if model.records_alias_enabled}

    def find_pid_type_from_pid(self, pid_value: str) -> str:
        """Given a PID value, get its associated PID type.

        This method requires that there are no duplicities in the PID values
        across models.
        """
        return cast("str", self._filter_model_pid(pid_value=pid_value).pid_type)

    def find_pid_from_uuid(self, uuid: UUID) -> PersistentIdentifier:
        """Given an object UUID, get its associated PID."""
        return self._filter_model_pid(object_uuid=uuid)

    def _filter_model_pid(self, **filter_kwargs: Any) -> PersistentIdentifier:
        """Filter PIDs based on the provided criteria and return only one that matches.

        Select persistent identifiers from the DB and return the one that is associated
        with any service registered within oarepo_runtime. If no such PID exists,
        an error is raised.

        If the filter matches multiple services, an error is raised.
        """
        pids = PersistentIdentifier.query.filter_by(**filter_kwargs).all()

        filtered_pids = [pid for pid in pids if pid.pid_type in self.record_class_by_pid_type]
        if not filtered_pids:
            raise PIDDoesNotExistError(
                None,
                filter_kwargs,
                "The pid value/record uuid is not associated with any record.",
            )

        if len(filtered_pids) > 1:
            raise PIDDoesNotExistError(
                None,
                filter_kwargs,
                f"Multiple records found for pid value/record uuid: {filtered_pids}",
            )
        return filtered_pids[0]

    @property
    def services(self) -> dict[str, Service]:
        """Return the services registered in the extension."""
        _services = current_service_registry._services  # type: ignore[attr-defined]  # noqa: SLF001
        return cast("dict[str, Service]", _services)

    def get_record_service_for_record(self, record: Any) -> RecordService:
        """Retrieve the associated service for a given record."""
        if record is None:
            raise ValueError("Need to pass a record instance, got None")
        return self.get_record_service_for_record_class(type(record))

    def get_file_service_for_record(self, record: Any) -> FileService | None:
        """Return the file service for the given record (draft or published)."""
        model = self.models_by_record_class.get(type(record))
        if not model:
            raise KeyError(f"No model found for record class '{type(record).__name__}'.")
        is_draft = getattr(record, "is_draft", False)
        if is_draft:
            return model.draft_file_service
        return model.file_service

    def get_record_service_for_record_class(self, record_cls: type[RecordBase]) -> RecordService:
        """Retrieve the service associated with a given record class."""
        for t in record_cls.mro():
            if t is RecordBase:
                break
            if t in self.models_by_record_class:
                model = self.models_by_record_class[t]
                return model.service
        raise KeyError(f"No service found for record class '{record_cls.__name__}'.")

    @cached_property
    def published_indices(self) -> set[str]:
        """Return the set of published indices for RDM-compatible records only."""
        indices = set()
        for model in self.rdm_models:
            indices.add(model.record_cls.index.search_alias)  # type: ignore[attr-defined]
        return indices

    @cached_property
    def draft_indices(self) -> set[str]:
        """Return the set of draft indices for RDM-compatible records only."""
        indices = set()
        for model in self.rdm_models:
            if model.draft_cls is not None:
                indices.add(model.draft_cls.index.search_alias)  # type: ignore[attr-defined]
        return indices
