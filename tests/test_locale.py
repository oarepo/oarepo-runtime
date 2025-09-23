#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import marshmallow as ma
import pytz
from babel import Locale

from oarepo_runtime.proxies import current_timezone
from oarepo_runtime.services.schema.ui import (
    LocalizedDate,
    LocalizedDateTime,
    LocalizedTime,
    current_default_locale,
)


class TestSchema(ma.Schema):
    """Test schema class for testing."""

    dt = LocalizedDate()
    dtm = LocalizedDateTime()
    tm = LocalizedTime()


def replace_ws(d):
    """Replace white spaces."""
    return {k: v.replace("\u202f", " ") for k, v in d.items()}


def test_localized_date(app):
    current_timezone.set(pytz.timezone("Europe/London"))
    input_data = {"dt": "2020-01-31", "tm": "12:21", "dtm": "2020-01-31T12:21"}
    assert replace_ws(TestSchema(context={"locale": Locale("en")}).dump(input_data)) == {
        "dt": "Jan 31, 2020",
        "tm": "12:21:00 PM",
        "dtm": "Jan 31, 2020, 12:21:00 PM",
    }
    input_data = {"dt": "2020-01-31", "tm": "12:21", "dtm": "2020-01-31T12:21"}
    assert replace_ws(TestSchema(context={"locale": Locale("cs")}).dump(input_data)) == {
        "dt": "31. 1. 2020",
        "dtm": "31. 1. 2020 12:21:00",
        "tm": "12:21:00",
    }


def test_localized_date_timezone(app):
    current_timezone.set(pytz.timezone("Europe/Prague"))
    input_data = {"dt": "2020-01-31", "tm": "12:21", "dtm": "2020-01-31T12:21"}
    assert replace_ws(TestSchema(context={"locale": Locale("en")}).dump(input_data)) == {
        "dt": "Jan 31, 2020",
        "tm": "12:21:00 PM",
        "dtm": "Jan 31, 2020, 1:21:00 PM",
    }
    input_data = {"dt": "2020-06-29", "tm": "12:21", "dtm": "2020-06-29T12:21"}
    assert replace_ws(TestSchema(context={"locale": Locale("en")}).dump(input_data)) == {
        "dt": "Jun 29, 2020",
        "tm": "12:21:00 PM",
        "dtm": "Jun 29, 2020, 2:21:00 PM",
    }


def test_default_locale(app):
    with app.app_context():
        locale = current_default_locale()
        assert locale == "en"

        app.config["BABEL_DEFAULT_LOCALE"] = "cs"
        locale = current_default_locale()
        assert locale == "cs"
