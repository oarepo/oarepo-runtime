import functools
import re
from datetime import datetime
from idutils import normalize_pid
from isbnlib import canonical, mask

from marshmallow.exceptions import ValidationError
from marshmallow_utils.fields.edtfdatestring import EDTFValidator

from invenio_i18n import gettext as _


def validate_identifier(value):
    try:
        if value["scheme"].lower() == "isbn":
            canonical_isbn = canonical(value["identifier"])
            value["identifier"] = mask(canonical_isbn)
            return value["identifier"]

        original_identifier = (value["identifier"] or '').strip()
        normalized_identifier = normalize_pid(
            value["identifier"], value["scheme"].lower()
        )
        if original_identifier and not normalized_identifier:
            # the normalize_pid library has problems with isbn - does not raise an exception
            # but returns an empty string
            raise ValueError()
        value["identifier"] = normalized_identifier
    except:
        raise ValidationError({
            "identifier": _("Invalid value %(identifier)s of identifier type %(type)s") % {"identifier": value['identifier'], "type": value['scheme']}
        })
    return value


def validate_date(date_format):
    def validate(value):
        try:
            datetime.strptime(value, date_format)
        except Exception as e:
            raise ValidationError(
                f"Invalid date/time format, expecting {date_format}, got {value}"
            ) from e

    return validate


def validate_datetime(value):
    try:
        datetime.fromisoformat(value)
    except Exception as e:
        raise ValidationError(
            f"Invalid datetime format, expecting iso format, got {value}"
        ) from e


class CachedMultilayerEDTFValidator(EDTFValidator):
    @functools.lru_cache(maxsize=1024)
    def __call__(self, value):
        if re.match(r"^\d{4}$", value):
            return value
        try:
            datetime.strptime(value, "%Y-%m-%d")
            return value
        except:
            return super().__call__(value)