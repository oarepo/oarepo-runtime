import pytest
from edtf import Date, DateAndTime, Interval
from marshmallow.exceptions import ValidationError

from oarepo_runtime.services.schema.validation import (
    validate_date,
    validate_datetime,
    CachedMultilayerEDTFValidator,
)


def test_date_validation():
    validator = validate_date("%Y-%m-%d")
    validator("1999-01-01")
    with pytest.raises(ValidationError):
        validator("1999-31-31")


def test_datetime_validation():
    validate_datetime("1990-01-02T12:23:01+02:00")
    with pytest.raises(ValidationError):
        validate_datetime("2000-01-02A")
    with pytest.raises(ValidationError):
        validate_datetime("abc")


def test_edtf_validation():
    validator = CachedMultilayerEDTFValidator(types=[Date, DateAndTime, Interval])
    validator("2000")
    validator("2000-02")
    validator("2000-02-15")
    validator("2000-02-15T12:20:15")
    validator("2004-01-01T10:10:10+05:00")
    validator("1979-08-28/1979-09-25")
