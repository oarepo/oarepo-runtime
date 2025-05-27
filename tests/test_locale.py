import marshmallow as ma
from flask import g
from invenio_i18n.ext import current_i18n
from oarepo_runtime.i18n import get_locale
from oarepo_runtime.proxies import current_timezone
from oarepo_runtime.services.schema.ui import (
    LocalizedDate,
    LocalizedDateTime,
    LocalizedEnum,
    LocalizedTime,
)
import pytz

class TestSchema(ma.Schema):
    dt = LocalizedDate()
    dtm = LocalizedDateTime()
    tm = LocalizedTime()


def replace_ws(d):
    return {k: v.replace("\u202f", " ") for k, v in d.items()}


def clear_babel_context():
    # for invenio 12
    try:
        from flask_babel import SimpleNamespace
    except ImportError:
        return
    g._flask_babel = SimpleNamespace()


def test_localized_date(app):
    clear_babel_context()
    current_timezone.set(pytz.timezone("Europe/London"))
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

    input_data = {"dt": "2020-01-31", "tm": "12:21", "dtm": "2020-01-31T12:21"}
    clear_babel_context()
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        assert current_i18n.language == "cs"
        assert replace_ws(
            TestSchema(context={"locale": get_locale()}).dump(input_data)
        ) == {
            "dt": "31. 1. 2020",
            "dtm": "31. 1. 2020 12:21:00",
            "tm": "12:21:00",
        }

def test_localized_date_timezone(app):
    clear_babel_context()
    current_timezone.set(pytz.timezone("Europe/Prague"))
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        assert current_i18n.language == "en"
        input_data = {"dt": "2020-01-31", "tm": "12:21", "dtm": "2020-01-31T12:21"}
        assert replace_ws(
            TestSchema(context={"locale": get_locale()}).dump(input_data)
        ) == {
            "dt": "Jan 31, 2020",
            "tm": "12:21:00 PM",
            "dtm": "Jan 31, 2020, 1:21:00 PM",
        }

class EnumSchema(ma.Schema):
    e = LocalizedEnum(value_prefix="e.")


def test_localized_enum(app):
    clear_babel_context()
    with app.test_request_context(headers=[("Accept-Language", "en")]):
        assert current_i18n.language == "en"
        input_data = {"e": "PCR"}
        assert EnumSchema().dump(input_data) == {
            "e": "PCR Method",
        }
    clear_babel_context()
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        assert current_i18n.language == "cs"
        assert EnumSchema().dump(input_data) == {
            "e": "Metoda PCR",
        }
