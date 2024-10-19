import marshmallow as ma

from marshmallow import fields as ma_fields
from marshmallow_utils.fields.nestedattr import NestedAttribute
from invenio_rdm_records.services.schemas.versions import VersionsSchema
from invenio_rdm_records.services.schemas.tombstone import DeletionStatusSchema
from invenio_rdm_records.services.schemas.access import AccessSchema


class RDMRecordMixin(ma.Schema):

    versions = NestedAttribute(VersionsSchema, dump_only=True)
    deletion_status = ma_fields.Nested(DeletionStatusSchema, dump_only=True)
    access = NestedAttribute(AccessSchema)