import langcodes
from marshmallow import Schema, ValidationError, fields, validates

"""
Marshmallow schema for multilingual strings. Consider moving this file to a library, not generating
it for each project.
"""


class I18nSchema(Schema):
    lang = fields.String(required=True)
    value = fields.String(required=True)

    @validates("lang")
    def validate_lang(self, value):
        if value != "_" and not langcodes.Language.get(value).is_valid():
            raise ValidationError("Invalid language code")


def I18nField(*args, **kwargs):
    return fields.List(fields.Nested(I18nSchema), *args, **kwargs)
