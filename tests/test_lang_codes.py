import pytest
from marshmallow.exceptions import ValidationError

from oarepo_runtime.services.schema.i18n_validation import lang_code_validator


def test_lang_code():
    lang_code_validator("cs")
    lang_code_validator("cze")
    with pytest.raises(ValidationError):
        lang_code_validator("unq")
