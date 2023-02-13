import pytest
from marshmallow.exceptions import ValidationError
from oarepo_runtime.validation.dates import validate_date


def test_date_validation():
    validator = validate_date("%Y-%m-%d")
    validator("1999-01-01")
    with pytest.raises(ValidationError):
        validator("1999-31-31")
