#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Record status module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from invenio_records.systemfields import SystemField

from .mapping import MappingSystemFieldMixin

if TYPE_CHECKING:
    from invenio_records.api import RecordBase
    from invenio_records.dumpers import Dumper


class RecordStatusSystemField(MappingSystemFieldMixin, SystemField):
    """A system field to track the status of a record (either 'draft' or 'published')."""

    @property
    def mapping(self) -> dict:
        """Return the mapping for the field in the search index."""
        return {
            self.attr_name: {
                "type": "keyword",
            },
        }

    @override
    def post_load(self, record: RecordBase, data: dict, loader: Dumper | None = None) -> None:
        data.pop(self.attr_name, None)

    @override
    def post_dump(self, record: RecordBase, data: dict, dumper: Dumper | None = None) -> None:
        if self.key is None:
            return
        data[self.attr_name] = getattr(record, self.key)

    def __get__(self, record: RecordBase | None, owner: Any = None) -> Any:
        """Access the attribute."""
        # Class access
        _ = owner
        if not isinstance(self.attr_name, str):
            raise TypeError  # pragma: no cover
        if record is None:
            return self
        return "draft" if getattr(record, "is_draft", False) else "published"
