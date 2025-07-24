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


class PublicationStatusSystemField(MappingSystemFieldMixin, SystemField):
    """A system field to track the status of a record (either 'draft' or 'published').

    The default key for this field is 'publication_status', but it can be customized.
    """

    def __init__(self, key: str | None = "publication_status"):
        """Initialize the system field with an optional key."""
        super().__init__(key)

    @property
    def mapping(self) -> dict:
        """Return the mapping for the field in the search index."""
        return {
            self.key: {
                "type": "keyword",
            },
        }

    @override
    def post_load(self, record: RecordBase, data: dict, loader: Dumper | None = None) -> None:
        data.pop(self.key, None)

    @override
    def post_dump(self, record: RecordBase, data: dict, dumper: Dumper | None = None) -> None:
        if self.key is None:
            return
        if not self.attr_name:
            raise ValueError("attr_name must be set for PublicationStatusSystemField")
        data[self.key] = getattr(record, self.attr_name)

    def __get__(self, record: RecordBase | None, owner: Any = None) -> Any:
        """Access the attribute."""
        if record is None:
            return self
        return "draft" if getattr(record, "is_draft", False) else "published"
