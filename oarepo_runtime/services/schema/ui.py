import datetime
import re

import marshmallow as ma
from babel.dates import format_date
from babel_edtf import format_edtf
from flask import current_app
from marshmallow_utils.fields import (
    BabelGettextDictField,
    FormatDate,
    FormatDatetime,
    FormatEDTF,
    FormatTime,
)
from marshmallow_utils.fields.babel import BabelFormatField

from oarepo_runtime.i18n import gettext


def current_default_locale():
    """Get the Flask app's default locale."""
    if current_app:
        return current_app.config.get("BABEL_DEFAULT_LOCALE", "en")
    # Use english by default if not specified
    return "en"


class LocalizedMixin:
    def __init__(self, *args, locale=None, **kwargs):
        super().__init__(*args, locale=locale, **kwargs)

    @property
    def locale(self):
        if self._locale:
            return self._locale
        if self.parent:
            if "locale" in self.context:
                return self.context["locale"]
        return current_default_locale()


# localized date field
class LocalizedDate(LocalizedMixin, FormatDate):
    pass


class FormatTimeString(FormatTime):
    def parse(self, value, as_time=False, as_date=False, as_datetime=False):
        if value and isinstance(value, str) and as_time == True:
            match = re.match(
                r"^(\d|0\d|1\d|2[0-3]):(\d|[0-5]\d|60)(:(\d|[0-5]\d|60))?$", value
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

    def parse(self, value, **kwargs):
        # standard parsing is too lenient, for example returns "2000-01-01" for input "2000"
        if re.match("^[0-9]+-[0-9]+-[0-9]+", value):
            return super().parse(value, **kwargs)
        raise ValueError("Not a valid date")


class LocalizedDateTime(LocalizedMixin, FormatDatetime):
    pass


class LocalizedTime(LocalizedMixin, FormatTimeString):
    pass


class LocalizedEDTF(LocalizedMixin, MultilayerFormatEDTF):
    pass


class LocalizedEDTFTime(LocalizedMixin, MultilayerFormatEDTF):
    pass


class LocalizedEDTFInterval(LocalizedMixin, FormatEDTF):
    pass


class LocalizedEDTFTimeInterval(LocalizedMixin, FormatEDTF):
    pass


class PrefixedGettextField(BabelGettextDictField):
    def __init__(self, *, value_prefix, locale, default_locale, **kwargs):
        super().__init__(locale, default_locale, **kwargs)
        self.value_prefix = value_prefix

    def _serialize(self, value, attr, obj, **kwargs):
        if value:
            value = f"{self.value_prefix}{value}"
        return gettext(value)


class LocalizedEnum(LocalizedMixin, PrefixedGettextField):
    pass

    def __init__(self, **kwargs):
        super().__init__(default_locale=current_default_locale, **kwargs)


if False:  # NOSONAR
    # just for the makemessages to pick up the translations
    translations = [_("True"), _("False")]


class InvenioUISchema(ma.Schema):
    id = ma.fields.Str()
    created = LocalizedDateTime(dump_only=True)
    updated = LocalizedDateTime(dump_only=True)
    links = ma.fields.Raw(dump_only=True)
    revision_id = ma.fields.Integer(dump_only=True)
