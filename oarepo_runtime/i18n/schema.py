from functools import lru_cache

import langcodes
from marshmallow import Schema, ValidationError, fields, validates

"""
Marshmallow schema for multilingual strings. Consider moving this file to a library, not generating
it for each project.
"""


@lru_cache
def get_i18n_schema(lang_field, value_field):
    @validates(lang_field)
    def validate_lang(self, value):
        if value != "_" and not langcodes.Language.get(value).is_valid():
            raise ValidationError("Invalid language code")

    return type(
        f"I18nSchema_{lang_field}_{value_field}",
        (Schema,),
        {
            "validate_lang": validate_lang,
            lang_field: fields.String(required=True),
            value_field: fields.String(required=True),
        },
    )


def MultilingualField(  # NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
    return fields.List(
        fields.Nested(get_i18n_schema(lang_field, value_field)),
        **kwargs,
    )


def I18nStrField(*args, lang_field="lang", value_field="value", **kwargs):  # NOSONAR
    return fields.Nested(
        get_i18n_schema(lang_field, value_field),
        *args,
        **kwargs,
    )
