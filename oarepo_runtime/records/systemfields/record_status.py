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


class RecordStatusResult:
    """Status result of a record."""

    def __init__(self, record: RecordBase, attr_name: str):
        """Initialize a new instance of the RecordStatusResult class.

        Args:
            record (Record): The record whose status is being tracked.
            attr_name (str): The name of the attribute representing the record's status.

        """
        self.record = record
        self.attr_name = attr_name


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
    def post_load(self, record: RecordBase, data: dict, loader: Any = None) -> None:
        data.pop(self.attr_name, None)

    @override
    def post_dump(
        self, record: RecordBase, data: dict, dumper: Dumper | None = None
    ) -> None:
        is_draft = getattr(record, "is_draft", False)

        if is_draft:  # pylint: ignore[attr-defined]
            data[self.attr_name] = "draft"
        else:
            data[self.attr_name] = "published"

    def __get__(self, record: RecordBase | None, owner: Any = None) -> Any:
        """Access the attribute."""
        # Class access
        _ = owner
        if not isinstance(self.attr_name, str):
            raise TypeError
        if record is None:
            return self
        return RecordStatusResult(record, self.attr_name)
