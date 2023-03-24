import langcodes
from marshmallow import Schema, ValidationError, fields, validates
from flask_babelex import get_locale
from flask import current_app


class I18nUISchema(Schema):
    lang = fields.String(required=True)
    value = fields.String(required=True)

    @validates("lang")
    def validate_lang(self, value):
        if value != "_" and not langcodes.Language.get(value).is_valid():
            raise ValidationError("Invalid language code")


def I18nUIField(*args, **kwargs):  # NOSONAR
    return fields.List(fields.Nested(I18nUISchema), *args, **kwargs)


class I18nLocalizedUISchema(Schema):
    def _serialize(self, value, attr, obj, **kwargs):
        if not value:
            return None
        locale = get_locale().language
        for v in value:
            if locale == v["lang"]:
                return v["value"]
        locale = current_app.config["BABEL_DEFAULT_LOCALE"]
        for v in value:
            if locale == v["lang"]:
                return v["value"]
        return next(iter(value))["value"]


def I18nLocalizedUIField(*args, **kwargs):  # NOSONAR
    return fields.List(fields.Nested(I18nLocalizedUISchema), *args, **kwargs)
