import langcodes
from marshmallow.exceptions import ValidationError


def lang_code_validator(value):
    if value != "_" and not langcodes.Language.get(value).is_valid():
        raise ValidationError(f"Invalid language code {value}")
