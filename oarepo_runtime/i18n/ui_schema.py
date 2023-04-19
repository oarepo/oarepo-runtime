from functools import lru_cache

from flask import current_app
from flask_babelex import get_locale
from marshmallow import Schema, fields


@lru_cache
def get_i18n_ui_schema(lang_field, value_field):
    return type(
        f"I18nUISchema_{lang_field}_{value_field}",
        (Schema,),
        {
            lang_field: fields.String(required=True),
            value_field: fields.String(required=True),
        },
    )


def MultilingualUIField(  # NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
    return fields.List(
        fields.Nested(get_i18n_ui_schema(lang_field, value_field)),
        **kwargs,
    )


def I18nStrUIField(*args, lang_field="lang", value_field="value", **kwargs):  # NOSONAR
    return fields.Nested(
        get_i18n_ui_schema(lang_field, value_field),
        *args,
        **kwargs,
    )


@lru_cache
def get_i18n_localized_ui_schema(lang_field, value_field):
    class I18nLocalizedUISchema(Schema):
        def _serialize(self, value, attr=None, obj=None, **kwargs):
            if not value:
                return None
            locale = get_locale().language
            for v in value:
                if locale == v[lang_field]:
                    return v[value_field]
            locale = current_app.config["BABEL_DEFAULT_LOCALE"]
            for v in value:
                if locale == v[lang_field]:
                    return v[value_field]
            return next(iter(value))[value_field]

    # inherit to get a nice name for debugging
    return type(
        f"I18nLocalizedUISchema_{lang_field}_{value_field}",
        (I18nLocalizedUISchema,),
        {},
    )


def MultilingualLocalizedUIField(  # NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
    return fields.Nested(
        get_i18n_localized_ui_schema(lang_field, value_field), **kwargs
    )


def I18nStrLocalizedUIField(  # NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
    return fields.Nested(
        get_i18n_ui_schema(lang_field, value_field),
        *args,
        **kwargs,
    )
