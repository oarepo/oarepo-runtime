#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""System fields mapping."""

from __future__ import annotations

import inspect
from typing import TYPE_CHECKING

from invenio_records.dumpers import SearchDumperExt

if TYPE_CHECKING:
    from invenio_records_resources.records import Record


class MappingSystemFieldMixin:
    """Mixin class that provides default mapping, mapping settings, and dynamic templates for system fields."""

    @property
    def mapping(self) -> dict:
        """Return the default mapping for the system field."""
        return {}

    @property
    def mapping_settings(self) -> dict:
        """Return the default mapping settings for the system field."""
        return {}

    @property
    def dynamic_templates(self) -> list:
        """Return the default dynamic templates for the system field."""
        return []

    def search_dump(self, data: dict, record: Record) -> None:
        """Dump custom field."""

    def search_load(self, data: dict, record_cls: type[Record]) -> None:
        """Load custom field."""


class SystemFieldDumperExt(SearchDumperExt):
    """System field dumper."""

    def dump(self, record: Record, data: dict) -> None:
        """Dump custom fields."""
        for cf in inspect.getmembers(type(record), lambda x: isinstance(x, MappingSystemFieldMixin)):
            cf[1].search_dump(data, record=record)

    def load(self, data: dict, record_cls: type[Record]) -> None:
        """Load custom fields."""
        for cf in inspect.getmembers(record_cls, lambda x: isinstance(x, MappingSystemFieldMixin)):
            cf[1].search_load(data, record_cls=record_cls)
