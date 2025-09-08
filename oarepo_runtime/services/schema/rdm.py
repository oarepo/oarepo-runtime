from functools import partial

import marshmallow as ma
from invenio_i18n import gettext as _
from invenio_i18n.selectors import get_locale
from invenio_rdm_records.services.schemas.metadata import record_identifiers_schemes
from invenio_rdm_records.services.schemas.tombstone import DeletionStatusSchema
from invenio_rdm_records.services.schemas.versions import VersionsSchema
from invenio_vocabularies.contrib.awards.schema import AwardRelationSchema
from invenio_vocabularies.contrib.funders.schema import FunderRelationSchema
from marshmallow import fields as ma_fields
from marshmallow import pre_load
from marshmallow_utils.fields import (
    IdentifierSet,
)
from marshmallow_utils.fields.nestedattr import NestedAttribute
from marshmallow_utils.schemas.identifier import IdentifierSchema

from .i18n import MultilingualField


class RDMRecordMixin(ma.Schema):
    versions = NestedAttribute(VersionsSchema, dump_only=True)
    deletion_status = ma_fields.Nested(DeletionStatusSchema, dump_only=True)


class MultilingualAwardSchema(AwardRelationSchema):
    class Meta:
        unknown = ma.RAISE

    @pre_load()
    def convert_to_multilingual(self, data, many, **kwargs):
        if "title" in data and type(data["title"]) is str:
            lang = get_locale()
            data["title"] = {lang: data["title"]}
        return data


class FundingSchema(ma.Schema):
    """Funding schema."""

    funder = ma_fields.Nested(FunderRelationSchema, required=True)
    award = ma_fields.Nested(MultilingualAwardSchema)


class RecordIdentifierField(IdentifierSet):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ma.fields.Nested(
                partial(IdentifierSchema, allowed_schemes=record_identifiers_schemes)
            ),
            *args,
            **kwargs,
        )


class RelatedRecordIdentifierField(IdentifierSet):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ma.fields.Nested(
                partial(IdentifierSchema, allowed_schemes=record_identifiers_schemes)
            ),
            *args,
            **kwargs,
        )


class RDMSubjectSchema(ma.Schema):
    """Subject ui schema."""

    class Meta:
        unknown = ma.RAISE

    _id = ma.fields.String(data_key="id")

    subject = MultilingualField()