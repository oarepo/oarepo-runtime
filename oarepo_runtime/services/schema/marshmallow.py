import marshmallow as ma
from invenio_records_resources.services.records.schema import (
    BaseRecordSchema as InvenioBaseRecordSchema,
)


class BaseRecordSchema(InvenioBaseRecordSchema):
    """Base record schema - in addition to invenio exposes $schema as well."""

    _schema = ma.fields.Str(attribute="$schema", data_key="$schema")
