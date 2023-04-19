import functools
import re
from datetime import datetime

from marshmallow.exceptions import ValidationError
from marshmallow_utils.fields.edtfdatestring import EDTFValidator


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
