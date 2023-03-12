from datetime import datetime

from marshmallow.exceptions import ValidationError


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
