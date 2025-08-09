#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.

"""Test i18n marshmallow fields."""

from __future__ import annotations

import pytest
from marshmallow import Schema, ValidationError, fields
from werkzeug.utils import ImportStringError

from oarepo_runtime.services.schema.i18n import (
    I18nStrField,
    MultilingualField,
    get_i18n_schema,
)


def test_get_i18n_schema_default_params():
    """Test get_i18n_schema with default parameters."""
    schema_class = get_i18n_schema("lang", "value")

    assert schema_class is not None
    assert issubclass(schema_class, Schema)
    assert schema_class.__name__ == "I18nSchema_lang_value"

    # Check that schema has the expected fields
    schema = schema_class()
    assert "lang" in schema.fields
    assert "value" in schema.fields
    assert isinstance(schema.fields["lang"], fields.String)


def test_get_i18n_schema_custom_params():
    """Test get_i18n_schema with custom parameters."""
    schema_class = get_i18n_schema("language", "text", "marshmallow.fields.String")

    assert schema_class is not None
    assert issubclass(schema_class, Schema)
    assert schema_class.__name__ == "I18nSchema_language_text"

    # Check that schema has the expected fields
    schema = schema_class()
    assert "language" in schema.fields
    assert "text" in schema.fields
    assert isinstance(schema.fields["language"], fields.String)
    assert isinstance(schema.fields["text"], fields.String)


def test_get_i18n_schema_caching():
    """Test that get_i18n_schema properly caches results."""
    schema_class1 = get_i18n_schema("lang", "value")
    schema_class2 = get_i18n_schema("lang", "value")

    # Should return the same class instance due to caching
    assert schema_class1 is schema_class2


def test_get_i18n_schema_invalid_field_class():
    """Test get_i18n_schema with invalid field class."""
    with pytest.raises(ImportStringError):
        get_i18n_schema("lang", "value", "nonexistent.field.Class")


def test_i18n_schema_validation_valid_language():
    """Test validation with valid language codes."""
    schema_class = get_i18n_schema("lang", "value", "marshmallow.fields.String")
    schema = schema_class()

    valid_data = [
        {"lang": "en", "value": "Hello"},
        {"lang": "cs", "value": "Ahoj"},
        {"lang": "de", "value": "Hallo"},
        {"lang": "fr", "value": "Bonjour"},
        {"lang": "_", "value": "Universal"},  # Special case
    ]

    for data in valid_data:
        result = schema.load(data)
        assert result == data


def test_i18n_schema_validation_invalid_language():
    """Test validation with invalid language codes."""
    schema_class = get_i18n_schema("lang", "value", "marshmallow.fields.String")
    schema = schema_class()

    invalid_data = [
        {"lang": "invalid", "value": "Hello"},
        {"lang": "xyz", "value": "Hello"},
        {"lang": "english", "value": "Hello"},
    ]

    for data in invalid_data:
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        assert "Invalid language code" in str(exc_info.value)


def test_i18n_schema_validation_missing_fields():
    """Test validation when required fields are missing."""
    schema_class = get_i18n_schema("lang", "value", "marshmallow.fields.String")
    schema = schema_class()

    invalid_data = [
        {"lang": "en"},  # Missing value
        {"value": "Hello"},  # Missing lang
        {},  # Missing both
        {"lang": "", "value": "Hello"},  # Empty lang
        {"lang": "en", "value": ""},  # Empty value
    ]

    for data in invalid_data:
        with pytest.raises(ValidationError) as exc_info:
            schema.load(data)
        errors = exc_info.value.messages
        assert "Both language and text must be provided." in (errors.get("lang", []) + errors.get("value", []))


def test_i18n_schema_different_field_names():
    """Test schema with different field names."""
    schema_class = get_i18n_schema("language", "content", "marshmallow.fields.String")
    schema = schema_class()

    valid_data = {"language": "en", "content": "Hello World"}
    result = schema.load(valid_data)
    assert result == valid_data

    # Test with missing fields using custom names
    with pytest.raises(ValidationError):
        schema.load({"language": "en"})  # Missing content


def test_multilingual_field_basic():
    """Test basic MultilingualField functionality."""
    field = MultilingualField()

    assert isinstance(field, fields.List)
    assert isinstance(field.inner, fields.Nested)


def test_multilingual_field_with_custom_params():
    """Test MultilingualField with custom parameters."""
    field = MultilingualField(
        lang_name="language",
        value_name="text",
        value_field="marshmallow.fields.String",
    )

    assert isinstance(field, fields.List)
    assert isinstance(field.inner, fields.Nested)


def test_multilingual_field_validation():
    """Test MultilingualField validation."""

    class TestSchema(Schema):
        multilingual = MultilingualField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    # Valid data
    valid_data = {
        "multilingual": [
            {"lang": "en", "value": "Hello"},
            {"lang": "cs", "value": "Ahoj"},
        ]
    }
    result = schema.load(valid_data)
    assert result == valid_data


def test_multilingual_field_validation_with_invalid_item():
    """Test MultilingualField validation with invalid items."""

    class TestSchema(Schema):
        multilingual = MultilingualField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    # Invalid data - one item has invalid language
    invalid_data = {
        "multilingual": [
            {"lang": "en", "value": "Hello"},
            {"lang": "invalid", "value": "Test"},  # Invalid language
        ]
    }

    with pytest.raises(ValidationError):
        schema.load(invalid_data)


def test_multilingual_field_empty_list():
    """Test MultilingualField with empty list."""

    class TestSchema(Schema):
        multilingual = MultilingualField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    valid_data = {"multilingual": []}
    result = schema.load(valid_data)
    assert result == valid_data


def test_multilingual_field_with_kwargs():
    """Test MultilingualField with additional kwargs."""
    field = MultilingualField(
        required=True,
        allow_none=False,
        lang_name="lang",
        value_name="value",
        value_field="marshmallow.fields.String",
    )

    assert field.required is True
    assert field.allow_none is False


def test_i18n_str_field_basic():
    """Test basic I18nStrField functionality."""
    field = I18nStrField()

    assert isinstance(field, fields.Nested)


def test_i18n_str_field_with_custom_params():
    """Test I18nStrField with custom parameters."""
    field = I18nStrField(
        lang_name="language",
        value_name="text",
        value_field="marshmallow.fields.String",
    )

    assert isinstance(field, fields.Nested)


def test_i18n_str_field_validation():
    """Test I18nStrField validation."""

    class TestSchema(Schema):
        title = I18nStrField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    # Valid data
    valid_data = {"title": {"lang": "en", "value": "Hello World"}}
    result = schema.load(valid_data)
    assert result == valid_data


def test_i18n_str_field_validation_invalid():
    """Test I18nStrField validation with invalid data."""

    class TestSchema(Schema):
        title = I18nStrField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    # Invalid data - missing value
    invalid_data = {"title": {"lang": "en"}}

    with pytest.raises(ValidationError):
        schema.load(invalid_data)


def test_i18n_str_field_with_args_and_kwargs():
    """Test I18nStrField with additional args and kwargs."""
    field = I18nStrField(
        required=True,
        allow_none=False,
        lang_name="lang",
        value_name="value",
        value_field="marshmallow.fields.String",
    )

    assert field.required is True
    assert field.allow_none is False


def test_i18n_str_field_different_field_names():
    """Test I18nStrField with different field names."""

    class TestSchema(Schema):
        description = I18nStrField(
            lang_name="language",
            value_name="content",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    valid_data = {"description": {"language": "cs", "content": "Popis"}}
    result = schema.load(valid_data)
    assert result == valid_data


def test_schema_with_multiple_i18n_fields():
    """Test schema with multiple i18n fields."""

    class DocumentSchema(Schema):
        title = I18nStrField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )
        descriptions = MultilingualField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = DocumentSchema()

    valid_data = {
        "title": {"lang": "en", "value": "Document Title"},
        "descriptions": [
            {"lang": "en", "value": "English description"},
            {"lang": "cs", "value": "Český popis"},
        ],
    }

    result = schema.load(valid_data)
    assert result == valid_data


def test_complex_nested_scenario():
    """Test complex nested scenario with various field types."""

    class ComplexSchema(Schema):
        simple_title = I18nStrField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )
        alternative_titles = MultilingualField(
            lang_name="language",
            value_name="text",
            value_field="marshmallow.fields.String",
        )
        metadata = fields.Dict()

    schema = ComplexSchema()

    complex_data = {
        "simple_title": {"lang": "en", "value": "Main Title"},
        "alternative_titles": [
            {"language": "en", "text": "Alternative English Title"},
            {"language": "de", "text": "Deutscher Alternativtitel"},
        ],
        "metadata": {"author": "Test Author"},
    }

    result = schema.load(complex_data)
    assert result == complex_data


@pytest.mark.parametrize(
    ("lang_code", "expected_valid"),
    [
        ("en", True),
        ("cs", True),
        ("de-DE", True),
        ("zh-CN", True),
        ("_", True),  # Special universal language
        ("invalid", False),
        ("xyz", False),
        ("", False),
        ("toolongcode", False),
    ],
)
def test_language_code_validation_parametrized(lang_code, expected_valid):
    """Test language code validation with various codes."""
    schema_class = get_i18n_schema("lang", "value", "marshmallow.fields.String")
    schema = schema_class()

    data = {"lang": lang_code, "value": "Test value"}

    if expected_valid:
        result = schema.load(data)
        assert result == data
    else:
        with pytest.raises(ValidationError):
            schema.load(data)
