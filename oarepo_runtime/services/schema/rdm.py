import marshmallow as ma

from marshmallow import fields as ma_fields
from marshmallow import pre_load
from marshmallow_utils.fields.nestedattr import NestedAttribute
from invenio_rdm_records.services.schemas.versions import VersionsSchema
from invenio_rdm_records.services.schemas.tombstone import DeletionStatusSchema
from invenio_rdm_records.services.schemas.access import AccessSchema
from invenio_vocabularies.contrib.awards.schema import AwardRelationSchema
from invenio_vocabularies.contrib.funders.schema import FunderRelationSchema
from invenio_i18n.selectors import get_locale


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
