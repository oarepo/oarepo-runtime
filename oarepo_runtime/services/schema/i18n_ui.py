from functools import lru_cache

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


def MultilingualUIField(  # noqa NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
    return fields.List(
        fields.Nested(get_i18n_ui_schema(lang_field, value_field)),
        **kwargs,
    )


def I18nStrUIField(  # noqa NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
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
            language = self.context["locale"].language
            for v in value:
                if language == v[lang_field]:
                    return v[value_field]
            return next(iter(value))[value_field]

    # inherit to get a nice name for debugging
    return type(
        f"I18nLocalizedUISchema_{lang_field}_{value_field}",
        (I18nLocalizedUISchema,),
        {},
    )


def MultilingualLocalizedUIField(  # noqa NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
    return fields.Nested(
        get_i18n_localized_ui_schema(lang_field, value_field), **kwargs
    )


def I18nStrLocalizedUIField(  # noqa NOSONAR
    *args, lang_field="lang", value_field="value", **kwargs
):
    return fields.Nested(
        get_i18n_ui_schema(lang_field, value_field),
        *args,
        **kwargs,
    )
