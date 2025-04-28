import datetime
import re

import marshmallow as ma
from babel.dates import format_date
from babel_edtf import format_edtf
from flask import current_app
from idutils import to_url
from invenio_rdm_records.records.systemfields.access.field.record import (
    AccessStatusEnum,
)
from invenio_rdm_records.resources.serializers.ui.fields import (
    UIObjectAccessStatus as InvenioUIObjectAccessStatus,
)
from invenio_rdm_records.services.schemas.parent import RDMParentSchema
from invenio_rdm_records.services.schemas.pids import PIDSchema
from invenio_rdm_records.services.schemas.record import validate_scheme
from invenio_rdm_records.services.schemas.versions import VersionsSchema
from marshmallow.fields import Dict, Nested
from marshmallow_utils.fields import (
    BabelGettextDictField,
    FormatDate,
    FormatDatetime,
    FormatEDTF,
    FormatTime,
    SanitizedUnicode,
)
from marshmallow_utils.fields.babel import BabelFormatField

from oarepo_runtime.i18n import gettext
from oarepo_runtime.i18n import lazy_gettext as _

from .marshmallow import RDMBaseRecordSchema


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

    def format_value(self, value):
        """Format the value, gracefully handling exceptions."""
        try:
            return super().format_value(value)
        except Exception as e:
            # Handle the exception gracefully
            current_app.logger.error(f"Error formatting value '{value}': {e}")
            return f"«Error formatting value '{value}'»"


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
    _schema = ma.fields.Str(attribute="$schema", data_key="$schema")
    id = ma.fields.Str()
    created = LocalizedDateTime(dump_only=True)
    updated = LocalizedDateTime(dump_only=True)
    links = ma.fields.Raw(dump_only=True)
    revision_id = ma.fields.Integer(dump_only=True)
    expanded = ma.fields.Raw(dump_only=True)


# seems not possible to avoid, as they have this hardcoded in their object,
# and translation keys are i.e. open, which gets translated to otevret
class UIObjectAccessStatus(InvenioUIObjectAccessStatus):
    @property
    def title(self):
        """Access status title."""
        return {
            AccessStatusEnum.OPEN: _("access.status.open"),
            AccessStatusEnum.EMBARGOED: _("access.status.embargoed"),
            AccessStatusEnum.RESTRICTED: _("access.status.restricted"),
            AccessStatusEnum.METADATA_ONLY: _("access.status.metadata-only"),
        }.get(self.access_status)


class AccessStatusField(ma.fields.Field):
    """Record access status."""

    def _serialize(self, value, attr, obj, **kwargs):
        """Serialise access status."""
        record_access_dict = obj.get("access")
        _files = obj.get("files", {})
        has_files = _files is not None and _files.get("enabled", False)
        if record_access_dict:
            record_access_status_ui = UIObjectAccessStatus(
                record_access_dict, has_files
            )
            return {
                "id": record_access_status_ui.id,
                "title_l10n": record_access_status_ui.title,
                "description_l10n": record_access_status_ui.description,
                "icon": record_access_status_ui.icon,
                "embargo_date_l10n": record_access_status_ui.embargo_date,
                "message_class": record_access_status_ui.message_class,
            }


# to be able to have access to entire pids object
class PIDsField(Dict):
    """Custom Dict field for PIDs that adds URLs after serialization."""

    def _serialize(self, value, attr, obj, **kwargs):
        """Serialize the PIDs and add URLs to them."""
        serialized = super()._serialize(value, attr, obj, **kwargs)

        if serialized:
            for scheme, pid in serialized.items():
                if scheme and pid and isinstance(pid, dict) and pid.get("identifier"):
                    url = to_url(pid["identifier"], scheme.lower(), url_scheme="https")
                    if url:
                        pid["url"] = url

        return serialized


class InvenioRDMParentUISchema(RDMParentSchema):
    """Parent schema."""

    pids = PIDsField(
        keys=SanitizedUnicode(validate=validate_scheme),
        values=Nested(PIDSchema),
    )


class InvenioRDMUISchema(InvenioUISchema, RDMBaseRecordSchema):
    """RDM UI schema."""

    is_draft = ma.fields.Boolean(dump_only=True)
    access_status = AccessStatusField(attribute="access", dump_only=True)
    versions = ma.fields.Nested(VersionsSchema, dump_only=True)
    pids = PIDsField(
        keys=SanitizedUnicode(validate=validate_scheme),
        values=Nested(PIDSchema),
    )
    parent = ma.fields.Nested(InvenioRDMParentUISchema)

    def hide_tombstone(self, data):
        """Hide tombstone info if the record isn't deleted and metadata if it is."""
        return data

    def default_nested(self, data):
        """Serialize fields as empty dict for partial drafts."""
        return data
