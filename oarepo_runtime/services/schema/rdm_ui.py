import marshmallow as ma
from oarepo_runtime.services.schema.marshmallow import DictOnlySchema

class NRIdentifierWithSchemaUISchema(ma.Schema):
    scheme = ma.fields.String(
        required=True,
    )
    identifier = ma.fields.String(required=True)

class NRAwardIdentifierUISchema(ma.Schema):
    identifier = ma.fields.String()

class NRAwardSubjectsUISchema(ma.Schema):
    _id = ma.fields.String(data_key="id")

    subject = ma.fields.String()

class NRAwardOrganizationsUISchema(ma.Schema):
    schema = ma.fields.String()

    _id = ma.fields.String(data_key="id")

    organization = ma.fields.String()

class NRFunderVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = ma.fields.String(data_key="id", attribute="id")

    _version = ma.fields.String(data_key="@v", attribute="@v")

    name = VocabularyI18nStrUIField()

    identifier = NRIdentifierWithSchemaUISchema()


class NRRoleVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = String(data_key="id", attribute="id")

    _version = String(data_key="@v", attribute="@v")

class NRAwardVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = String(data_key="id", attribute="id")

    _version = String(data_key="@v", attribute="@v")

    title = VocabularyI18nStrUIField()

    number = ma.fields.String()

    identifier = ma.fields.List(ma.fields.Nested(NRAwardIdentifierUISchema()))

    acronym = ma.fields.String()

    program = ma.fields.String()

    subjects = ma.fields.List(ma.fields.Nested(NRAwardSubjectsUISchema()))

    organizations = ma.fields.List(ma.fields.Nested(NRAwardOrganizationsUISchema()))


class NRFundersUISchema(ma.Schema):
    """Funding ui schema."""
    class Meta:
        unknown = ma.RAISE

    funder = ma_fields.Nested(lambda: NRFunderVocabularyUISchema())

    award = ma_fields.Nested(lambda: NRAwardVocabularyUISchema())


class NRPersonOrOrganizationsUISchema(ma.Schema):
    class Meta:
        unknown = ma.INCLUDE

    name = ma.fields.String()

    type = ma.fields.String()

    given_name = ma.fields.String()

    family_name = ma.fields.String()

    identifiers = ma.fields.List(ma.fields.Nested(NRIdentifierWithSchemaUISchema()))


class NRAffiliationsVocabularyUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.INCLUDE

    _id = ma.fields.String(data_key="id", attribute="id")

    _version = ma.fields.String(data_key="@v", attribute="@v")

    name = VocabularyI18nStrUIField()

class NRCreatorsUISchema(ma.Schema):
    """Funding ui schema."""
    class Meta:
        unknown = ma.RAISE

    role = ma.fields.Nested(lambda: NRRoleVocabularyUISchema())

    affiliations = ma.fields.List(ma_fields.Nested(lambda: NRAffiliationsVocabularyUISchema()))

    person_or_org = ma_fields.Nested(NRPersonOrOrganizationsUISchema())