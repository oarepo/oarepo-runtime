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

from typing import TYPE_CHECKING, override

if TYPE_CHECKING:
    from invenio_records.api import RecordBase
    from invenio_records.dumpers import Dumper
    from invenio_records.systemfields import SystemField
else:
    SystemField = object


class MappingSystemFieldMixin(SystemField):
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

    # The following methods are added just for typing purposes.
    @override
    def pre_dump(self, record: RecordBase, data: dict, dumper: Dumper | None = None) -> None:  # type: ignore[misc]
        """Dump record to the data - pre-dump phase."""

    @override
    def post_dump(self, record: RecordBase, data: dict, dumper: Dumper | None = None) -> None:  # type: ignore[misc]
        """Dump record to the data - post-dump phase."""

    @override
    def pre_load(self, data: dict, loader: Dumper | None = None) -> None:  # type: ignore[misc]
        """Load record from the data - pre-load phase."""

    @override
    def post_load(self, record: RecordBase, data: dict, loader: Dumper | None = None) -> None:  # type: ignore[misc]
        """Load record from the data - post-load phase."""
