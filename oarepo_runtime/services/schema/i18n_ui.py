from functools import lru_cache

from invenio_base.utils import obj_or_import_string
from marshmallow import Schema, fields


@lru_cache
def get_i18n_ui_schema(
    lang_name, value_name, value_field="marshmallow_utils.fields.SanitizedHTML"
):
    value_field_class = obj_or_import_string(value_field)
    return type(
        f"I18nUISchema_{lang_name}_{value_name}",
        (Schema,),
        {
            lang_name: fields.String(required=True),
            value_name: value_field_class(required=True),
        },
    )


def MultilingualUIField(  # noqa NOSONAR
    *args,
    lang_name="lang",
    value_name="value",
    value_field="marshmallow_utils.fields.SanitizedHTML",
    **kwargs,
):
    return fields.List(
        fields.Nested(get_i18n_ui_schema(lang_name, value_name, value_field)),
        **kwargs,
    )


def I18nStrUIField(  # noqa NOSONAR
    *args,
    lang_name="lang",
    value_name="value",
    value_field="marshmallow_utils.fields.SanitizedHTML",
    **kwargs,
):
    return fields.Nested(
        get_i18n_ui_schema(lang_name, value_name, value_field),
        *args,
        **kwargs,
    )


@lru_cache
def get_i18n_localized_ui_schema(lang_name, value_name):
    class I18nLocalizedUISchema(Schema):
        def _serialize(self, value, attr=None, obj=None, **kwargs):
            if not value:
                return None
            language = self.context["locale"].language
            for v in value:
                if language == v[lang_name]:
                    return v[value_name]
            return next(iter(value))[value_name]

    # inherit to get a nice name for debugging
    return type(
        f"I18nLocalizedUISchema_{lang_name}_{value_name}",
        (I18nLocalizedUISchema,),
        {},
    )


def MultilingualLocalizedUIField(  # noqa NOSONAR
    *args, lang_name="lang", value_name="value", **kwargs
):
    return fields.Nested(get_i18n_localized_ui_schema(lang_name, value_name), **kwargs)


def I18nStrLocalizedUIField(  # noqa NOSONAR
    *args, lang_name="lang", value_name="value", **kwargs
):
    return fields.Nested(
        get_i18n_ui_schema(lang_name, value_name),
        *args,
        **kwargs,
    )
