import marshmallow as ma
from oarepo_runtime.services.schema.marshmallow import DictOnlySchema
from oarepo_vocabularies.services.ui_schema import VocabularyI18nStrUIField
from idutils import to_url


class RDMIdentifierWithSchemaUISchema(ma.Schema):
    scheme = ma.fields.String(
        required=True,
    )
    identifier = ma.fields.String(required=True)

    @ma.post_dump
    def add_url(self, value, **kwargs):
        if "identifier" in value and "scheme" in value:
            url = to_url(
                value["identifier"], value["scheme"].lower(), url_scheme="https"
            )
            if url:
                value["url"] = url
        return value


class RDMAwardIdentifierUISchema(ma.Schema):
    identifier = ma.fields.String()


class RDMAwardSubjectUISchema(ma.Schema):
    _id = ma.fields.String(data_key="id")

    subject = ma.fields.String()


class RDMAwardOrganizationUISchema(ma.Schema):
    schema = ma.fields.String()

    _id = ma.fields.String(data_key="id")

    organization = ma.fields.String()


class RDMFunderVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = ma.fields.String(data_key="id", attribute="id")

    _version = ma.fields.String(data_key="@v", attribute="@v")

    name = ma.fields.String()

    identifiers = ma.fields.List(ma.fields.Nested(RDMIdentifierWithSchemaUISchema()))


class RDMRoleVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = ma.fields.String(data_key="id", attribute="id")

    _version = ma.fields.String(data_key="@v", attribute="@v")

    title = VocabularyI18nStrUIField()


class RDMAwardVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = ma.fields.String(data_key="id", attribute="id")

    _version = ma.fields.String(data_key="@v", attribute="@v")

    title = VocabularyI18nStrUIField()

    number = ma.fields.String()

    identifier = ma.fields.List(ma.fields.Nested(RDMAwardIdentifierUISchema()))

    acronym = ma.fields.String()

    program = ma.fields.String()

    subjects = ma.fields.List(ma.fields.Nested(RDMAwardSubjectUISchema()))

    organizations = ma.fields.List(ma.fields.Nested(RDMAwardOrganizationUISchema()))


class RDMFundersUISchema(ma.Schema):
    """Funding ui schema."""

    class Meta:
        unknown = ma.RAISE

    funder = ma.fields.Nested(lambda: RDMFunderVocabularyUISchema())

    award = ma.fields.Nested(lambda: RDMAwardVocabularyUISchema())


class RDMPersonOrOrganizationUISchema(ma.Schema):
    class Meta:
        unknown = ma.INCLUDE

    name = ma.fields.String()

    type = ma.fields.String()

    given_name = ma.fields.String()

    family_name = ma.fields.String()

    identifiers = ma.fields.List(ma.fields.Nested(RDMIdentifierWithSchemaUISchema()))


class RDMAffiliationVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = ma.fields.String(data_key="id", attribute="id")

    _version = ma.fields.String(data_key="@v", attribute="@v")

    name = ma.fields.String()


class RDMCreatorsUISchema(ma.Schema):
    """Funding ui schema."""

    class Meta:
        unknown = ma.RAISE

    role = ma.fields.Nested(lambda: RDMRoleVocabularyUISchema())

    affiliations = ma.fields.List(
        ma.fields.Nested(lambda: RDMAffiliationVocabularyUISchema())
    )

    person_or_org = ma.fields.Nested(RDMPersonOrOrganizationUISchema())
