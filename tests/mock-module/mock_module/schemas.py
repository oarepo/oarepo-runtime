# type: ignore  # noqa
#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Drafts-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Record schema."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

from invenio_drafts_resources.services.records.schema import (
    RecordSchema as BaseRecordSchema,
)
from marshmallow import Schema, fields, pre_load, validate
from marshmallow.utils import get_value
from marshmallow_utils.fields import NestedAttribute, SanitizedUnicode


class MetadataSchema(Schema):
    """Basic metadata schema class."""

    title = fields.Str(required=True, validate=validate.Length(min=3))


class FileMetadataSchema(Schema):
    """Schema for file metadata."""

    page = fields.Integer()
    type = fields.String()
    language = fields.String()
    encoding = fields.String()
    charset = fields.String()
    previewer = fields.String()
    width = fields.Integer()
    height = fields.Integer()


class FileSchema(Schema):
    """RDM-like File schema, not having access nor processors."""

    # File fields
    id = fields.String(attribute="file.id")
    checksum = fields.String(attribute="file.checksum")
    ext = fields.String(attribute="file.ext")
    size = fields.Integer(attribute="file.size")
    mimetype = fields.String(attribute="file.mimetype")
    storage_class = fields.String(attribute="file.storage_class")

    # FileRecord fields
    key = SanitizedUnicode()
    metadata = fields.Nested(FileMetadataSchema)


class FilesSchema(Schema):
    """Basic files schema class."""

    enabled = fields.Bool(missing=True)
    # allow unsetting
    default_preview = SanitizedUnicode(allow_none=True)

    order = fields.List(SanitizedUnicode())

    count = fields.Integer(dump_only=True)
    total_bytes = fields.Integer(dump_only=True)

    entries = fields.Dict(
        keys=SanitizedUnicode(),
        values=NestedAttribute(FileSchema),
        dump_only=True,
    )

    @pre_load
    def clean(self, data, **_kwargs: dict[str, Any]):
        """Remove dump_only fields.

        Why: We want to allow the output of a Schema dump, to be a valid input to a Schema load without causing strange issues.
        """  # noqa: E501
        for name, field in self.fields.items():
            if field.dump_only:
                data.pop(name, None)
        return data

    def get_attribute(self, obj, attr, default):
        """Override how attributes are retrieved when dumping.

        NOTE: We have to access by attribute because although we are loading
              from an external pure dict, but we are dumping from a data-layer
              object whose fields should be accessed by attributes and not
              keys. Access by key runs into FilesManager key access protection
              and raises.
        """
        value = getattr(obj, attr, default)

        if attr == "default_preview" and not value:
            return default

        return value


class RecordSchema(BaseRecordSchema):
    """Schema for records in JSON."""

    metadata = fields.Nested(MetadataSchema)
    files = fields.Nested(FilesSchema)
    media_files = fields.Nested(FilesSchema)

    @pre_load
    def clean_data(self, input_data, **_kwargs: Any) -> dict[str, Any]:
        """Remove dump_only fields."""
        data = deepcopy(input_data)
        data.pop("result_component", None)
        return data

    def get_attribute(self, obj, attr, default):
        """Override how attributes are retrieved when dumping.

        NOTE: We have to access by attribute because although we are loading
              from an external pure dict, but we are dumping from a data-layer
              object whose fields should be accessed by attributes and not
              keys. Access by key runs into FilesManager key access protection
              and raises.
        """
        if attr == "files":
            return getattr(obj, attr, default)
        return get_value(obj, attr, default)
