import marshmallow as ma
import pytest
from flask_babelex import get_locale
from invenio_i18n.ext import current_i18n

from oarepo_runtime.services.schema.ui import (
    LocalizedDate,
    LocalizedDateTime,
    LocalizedEnum,
    LocalizedTime,
)


class TestSchema(ma.Schema):
    dt = LocalizedDate()
    dtm = LocalizedDateTime()
    tm = LocalizedTime()


def replace_ws(d):
    return {k: v.replace("\u202f", " ") for k, v in d.items()}


def test_localized_date(app):
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        assert current_i18n.language == "en"
        input_data = {"dt": "2020-01-31", "tm": "12:21", "dtm": "2020-01-31T12:21"}
        assert replace_ws(
            TestSchema(context={"locale": get_locale()}).dump(input_data)
        ) == {
            "dt": "Jan 31, 2020",
            "tm": "12:21:00 PM",
            "dtm": "Jan 31, 2020, 12:21:00 PM",
        }
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        assert current_i18n.language == "cs"
        assert replace_ws(
            TestSchema(context={"locale": get_locale()}).dump(input_data)
        ) == {
            "dt": "31. 1. 2020",
            "dtm": "31. 1. 2020 12:21:00",
            "tm": "12:21:00",
        }


class EnumSchema(ma.Schema):
    e = LocalizedEnum(value_prefix="e.")


def test_localized_enum(app):
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        assert current_i18n.language == "en"
        input_data = {"e": "PCR"}
        assert EnumSchema().dump(input_data) == {
            "e": "PCR Method",
        }
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        assert current_i18n.language == "cs"
        assert EnumSchema().dump(input_data) == {
            "e": "Metoda PCR",
        }
