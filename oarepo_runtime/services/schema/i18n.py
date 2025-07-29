from functools import lru_cache

import langcodes
from invenio_base.utils import obj_or_import_string
from invenio_i18n import gettext as _
from marshmallow import Schema, ValidationError, fields, pre_load, validates

"""
Marshmallow schema for multilingual strings. Consider moving this file to a library, not generating
it for each project.
"""


@lru_cache
def get_i18n_schema(
    lang_name, value_name, value_field="marshmallow_utils.fields.SanitizedHTML"
):

    class I18nMixin:
        @validates(lang_name)
        def validate_lang(self, value):
            if value != "_" and not langcodes.Language.get(value).is_valid():
                raise ValidationError("Invalid language code")

        @pre_load
        def pre_load_func(self, data, **kwargs):
            if not data.get(lang_name) or not data.get(value_name):
                raise ValidationError(_("Both language and text must be provided."))
            return data

    value_field_class = obj_or_import_string(value_field)

    return type(
        f"I18nSchema_{lang_name}_{value_name}",
        (
            I18nMixin,
            Schema,
        ),
        {
            lang_name: fields.String(required=True),
            value_name: value_field_class(required=True),
        },
    )


def MultilingualField(  # noqa NOSONAR
    *args,
    lang_name="lang",
    value_name="value",
    value_field="marshmallow_utils.fields.SanitizedHTML",
    **kwargs,
):
    # TODO: args are not used but oarepo-model-builder-multilingual generates them
    # should be fixed there and subsequently removed here
    return fields.List(
        fields.Nested(get_i18n_schema(lang_name, value_name, value_field)),
        **kwargs,
    )


def I18nStrField(  # noqa NOSONAR
    *args,
    lang_name="lang",
    value_name="value",
    value_field="marshmallow_utils.fields.SanitizedHTML",
    **kwargs,
):
    return fields.Nested(
        get_i18n_schema(lang_name, value_name, value_field),
        *args,
        **kwargs,
    )
