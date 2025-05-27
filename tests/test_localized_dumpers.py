import datetime

import marshmallow

from oarepo_runtime.proxies import current_timezone
from oarepo_runtime.services.schema.ui import (
    LocalizedDate,
    LocalizedDateTime,
    LocalizedEDTF,
    LocalizedEDTFInterval,
    LocalizedEnum,
)
import pytz

def LocalizedSchema(locale, field, **kwargs):
    return type(
        f"LocalizedSchema_{field.__name__}",
        (marshmallow.Schema,),
        {"a": field(**kwargs)},
    )(context={"locale": locale})


def test_localized_date():
    # current default locale
    value = datetime.date.fromisoformat("1990-01-01")
    assert LocalizedDate().format_value(value) == "Jan 1, 1990"
    assert LocalizedDate(locale="en").format_value(value) == "Jan 1, 1990"
    assert LocalizedDate(locale="cs").format_value(value) == "1. 1. 1990"
    assert LocalizedSchema("en", LocalizedDate).dump({"a": value}) == {
        "a": "Jan 1, 1990"
    }
    assert LocalizedSchema("cs", LocalizedDate).dump({"a": value}) == {
        "a": "1. 1. 1990"
    }


def test_localized_date_with_app(app):
    with app.app_context():
        value = datetime.date.fromisoformat("1990-01-01")
        assert LocalizedDate().format_value(value) == "Jan 1, 1990"
        assert LocalizedDate(locale="en").format_value(value) == "Jan 1, 1990"
        assert LocalizedDate(locale="cs").format_value(value) == "1. 1. 1990"
        assert LocalizedSchema("en", LocalizedDate).dump({"a": value}) == {
            "a": "Jan 1, 1990"
        }
        assert LocalizedSchema("cs", LocalizedDate).dump({"a": value}) == {
            "a": "1. 1. 1990"
        }


def normalize_whitespace(s):
    if isinstance(s, str):
        return " ".join(s.split())
    if isinstance(s, dict):
        return {k: normalize_whitespace(v) for k, v in s.items()}
    if isinstance(s, list):
        return [normalize_whitespace(v) for v in s]
    return s


def test_localized_edtf():
    # LocalizedEDTF only outputs dates, not times
    assert LocalizedEDTF().format_value("2000") == "2000"
    assert normalize_whitespace(LocalizedEDTF().format_value("2000-01")) == "Jan 2000"
    assert (
        normalize_whitespace(LocalizedEDTF().format_value("2000-01-15"))
        == "Jan 15, 2000"
    )
    assert (
        normalize_whitespace(LocalizedEDTF().format_value("2000-02-15T12:20:15"))
        == "Feb 15, 2000"
    )
    assert (
        normalize_whitespace(LocalizedEDTF().format_value("2000-02-15T12:20:15+05:00"))
        == "Feb 15, 2000"
    )
    assert (
        normalize_whitespace(LocalizedEDTF().format_value("1979-08-28/1979-09-25"))
        == "Aug 28 – Sep 25, 1979"
    )

    assert LocalizedEDTF(locale="cs").format_value("2000") == "2000"
    assert (
        normalize_whitespace(LocalizedEDTF(locale="cs").format_value("2000-01"))
        == "leden 2000"
    )
    assert (
        normalize_whitespace(LocalizedEDTF(locale="cs").format_value("2000-01-15"))
        == "15. 1. 2000"
    )
    assert (
        normalize_whitespace(
            LocalizedEDTF(locale="cs").format_value("2000-02-15T12:20:15")
        )
        == "15. 2. 2000"
    )
    assert (
        normalize_whitespace(
            LocalizedEDTF(locale="cs").format_value("2000-02-15T12:20:15+05:00")
        )
        == "15. 2. 2000"
    )
    assert (
        normalize_whitespace(
            LocalizedEDTF(locale="cs").format_value("1979-08-28/1979-09-25")
        )
        == "28. 8. – 25. 9. 1979"
    )


def test_localized_datetime():
    # current default locale
    current_timezone.set(pytz.timezone("Etc/GMT-2"))
    value = "2000-02-15T12:20:15+02:00"
    assert (
        normalize_whitespace(LocalizedDateTime().format_value(value))
        == "Feb 15, 2000, 12:20:15 PM"
    )
    assert (
        normalize_whitespace(LocalizedDateTime(locale="en").format_value(value))
        == "Feb 15, 2000, 12:20:15 PM"
    )
    assert (
        normalize_whitespace(LocalizedDateTime(locale="cs").format_value(value))
        == "15. 2. 2000 12:20:15"
    )
    assert normalize_whitespace(
        LocalizedSchema("en", LocalizedDateTime).dump({"a": value})
    ) == {"a": "Feb 15, 2000, 12:20:15 PM"}
    assert normalize_whitespace(
        LocalizedSchema("cs", LocalizedDateTime).dump({"a": value})
    ) == {"a": "15. 2. 2000 12:20:15"}


def test_localized_edtf_interval():
    value = "1979-08-28/1979-09-25"
    assert (
        normalize_whitespace(LocalizedEDTFInterval().format_value(value))
        == "Aug 28 – Sep 25, 1979"
    )
    assert (
        normalize_whitespace(LocalizedEDTFInterval(locale="en").format_value(value))
        == "Aug 28 – Sep 25, 1979"
    )
    assert (
        normalize_whitespace(LocalizedEDTFInterval(locale="cs").format_value(value))
        == "28. 8. – 25. 9. 1979"
    )
    assert normalize_whitespace(
        LocalizedSchema("en", LocalizedEDTFInterval).dump({"a": value})
    ) == {"a": "Aug 28 – Sep 25, 1979"}
    assert normalize_whitespace(
        LocalizedSchema("cs", LocalizedEDTFInterval).dump({"a": value})
    ) == {"a": "28. 8. – 25. 9. 1979"}


def test_localized_enum():
    value = "a"
    assert LocalizedSchema("en", LocalizedEnum, value_prefix="aa.").dump(
        {"a": value}
    ) == {"a": "aa.a"}
    assert LocalizedSchema("cs", LocalizedEnum, value_prefix="aa.").dump(
        {"a": value}
    ) == {"a": "aa.a"}
