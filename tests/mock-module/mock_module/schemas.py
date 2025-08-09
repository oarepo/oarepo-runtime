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
from marshmallow_utils.fields import SanitizedUnicode


class MetadataSchema(Schema):
    """Basic metadata schema class."""

    title = fields.Str(required=True, validate=validate.Length(min=3))


class FilesSchema(Schema):
    """Basic files schema class."""

    enabled = fields.Bool(missing=True)
    # allow unsetting
    default_preview = SanitizedUnicode(allow_none=True)

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
