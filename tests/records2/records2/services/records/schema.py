import marshmallow as ma
from invenio_records_resources.services.records.schema import (
    BaseRecordSchema as InvenioBaseRecordSchema,
)
from marshmallow import fields as ma_fields

from oarepo_runtime.validation import validate_date


class Records2MetadataSchema(ma.Schema):
    """Records2MetadataSchema schema."""

    title = ma_fields.String()


class Records2Schema(InvenioBaseRecordSchema):
    """Records2Schema schema."""

    metadata = ma_fields.Nested(lambda: Records2MetadataSchema())
    created = ma_fields.String(validate=[validate_date("%Y-%m-%d")], dump_only=True)
    updated = ma_fields.String(validate=[validate_date("%Y-%m-%d")], dump_only=True)
