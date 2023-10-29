import datetime
import re

import marshmallow as ma
from babel.dates import format_date
from babel_edtf import format_edtf
from flask import current_app
from flask_babelex import gettext
from marshmallow_utils.fields import (
    BabelGettextDictField,
    FormatDate,
    FormatDatetime,
    FormatEDTF,
    FormatTime,
)
from marshmallow_utils.fields.babel import BabelFormatField


def current_default_locale():
    """Get the Flask app's default locale."""
    if current_app:
        return current_app.config.get("BABEL_DEFAULT_LOCALE", "en")
    # Use english by default if not specified
    return "en"


# localized date field
class LocalizedDate(FormatDate):
    @property
    def locale(self):
        return self.context["locale"]


class FormatTimeString(FormatTime):
    def parse(self, value, as_time=False, as_date=False, as_datetime=False):
        if value and isinstance(value, str) and as_time == True:
            match = re.match(
                r"^(\d|0\d|1[0-2]):(\d|[0-5]\d|60)(:(\d|[0-5]\d|60))?$", value
            )
            if match:
                value = datetime.time(
                    hour=int(match.group(1)),
                    minute=int(match.group(2)),
                    second=int(match.group(4)) if match.group(4) else 0,
                )

        return super().parse(value, as_time, as_date, as_datetime)


class MultilayerFormatEDTF(BabelFormatField):
    def format_value(self, value):
        try:
            return format_date(
                self.parse(value, as_date=True), format=self._format, locale=self.locale
            )
        except:
            return format_edtf(value, format=self._format, locale=self.locale)


class LocalizedEDTF(MultilayerFormatEDTF):
    @property
    def locale(self):
        return self.context["locale"]


class LocalizedTime(FormatTimeString):
    @property
    def locale(self):
        return self.context["locale"]


class LocalizedDateTime(FormatDatetime):
    @property
    def locale(self):
        return self.context["locale"]


class LocalizedEDTFInterval(FormatEDTF):
    @property
    def locale(self):
        return self.context["locale"]


class PrefixedGettextField(BabelGettextDictField):
    def __init__(self, *, value_prefix, locale, default_locale, **kwargs):
        super().__init__(locale, default_locale, **kwargs)
        self.value_prefix = value_prefix

    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            value = f"{self.value_prefix}{value}"
        return gettext(value)


class LocalizedEnum(PrefixedGettextField):
    @property
    def locale(self):
        return self.context["locale"]

    def __init__(self, **kwargs):
        super().__init__(locale=None, default_locale=current_default_locale, **kwargs)


if False:  # NOSONAR
    # just for the makemessages to pick up the translations
    translations = [_("True"), _("False")]


class InvenioUISchema(ma.Schema):
    id = ma.fields.Str()
    created = LocalizedDateTime(dump_only=True)
    updated = LocalizedDateTime(dump_only=True)
    links = ma.fields.Raw(dump_only=True)
    revision_id = ma.fields.Integer(dump_only=True)
