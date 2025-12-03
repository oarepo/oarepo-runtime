from flask_resources import BaseListSchema, MarshmallowSerializer
from flask_resources.serializers import JSONSerializer
from marshmallow import Schema, fields


class DescriptionSchema(Schema):
    description = fields.Str()


class TitleSchema(Schema):
    title = fields.Str()


class AuthorSchema(Schema):
    name = fields.Str()


class KeywordSchema(Schema):
    subject = fields.Str()


class DefaultRDMUISchema(Schema):
    doi = fields.Str(attribute="doi")
    publisher = fields.Str(attribute="publisher.name")
    publication_date = fields.Str(attribute="publicationYear")
    descriptions = fields.List(fields.Nested(DescriptionSchema))
    titles = fields.List(fields.Nested(TitleSchema))
    authors = fields.List(fields.Nested(AuthorSchema), attribute="creators")
    contributors = fields.List(fields.Nested(AuthorSchema), attribute="contributors")
    url = fields.Str(attribute="url")
    keywords = fields.List(fields.Nested(KeywordSchema), attribute="subjects")

    def dump(self, datacite_dict: dict, many: bool = None):
        return super().dump(obj=datacite_dict, many=many)


class RecordUISerializer(MarshmallowSerializer):
    """Marshmallow based DataCite schema v4.3 serializer for records."""

    def __init__(self, **options):
        """Constructor."""
        super().__init__(
            format_serializer_cls=JSONSerializer,
            object_schema_cls=DefaultRDMUISchema,
            list_schema_cls=BaseListSchema,
            **options,
        )
