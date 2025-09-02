#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test i18n UI marshmallow fields."""

from __future__ import annotations

from unittest.mock import Mock

import pytest
from marshmallow import Schema, fields
from werkzeug.utils import ImportStringError

from oarepo_runtime.services.schema.i18n_ui import (
    I18nStrLocalizedUIField,
    I18nStrUIField,
    MultilingualLocalizedUIField,
    MultilingualUIField,
    get_i18n_localized_ui_schema,
    get_i18n_ui_schema,
)


def test_get_i18n_ui_schema_default_params():
    """Test get_i18n_ui_schema with default parameters."""
    schema_class = get_i18n_ui_schema("lang", "value")

    assert schema_class is not None
    assert issubclass(schema_class, Schema)
    assert schema_class.__name__ == "I18nUISchema_lang_value"

    # Check that schema has the expected fields
    schema = schema_class()
    assert "lang" in schema.fields
    assert "value" in schema.fields
    assert isinstance(schema.fields["lang"], fields.String)
    assert schema.fields["lang"].required is True
    assert schema.fields["value"].required is True


def test_get_i18n_ui_schema_custom_params():
    """Test get_i18n_ui_schema with custom parameters."""
    schema_class = get_i18n_ui_schema("language", "text", "marshmallow.fields.String")

    assert schema_class is not None
    assert issubclass(schema_class, Schema)
    assert schema_class.__name__ == "I18nUISchema_language_text"

    # Check that schema has the expected fields
    schema = schema_class()
    assert "language" in schema.fields
    assert "text" in schema.fields
    assert isinstance(schema.fields["language"], fields.String)
    assert isinstance(schema.fields["text"], fields.String)
    assert schema.fields["language"].required is True
    assert schema.fields["text"].required is True


def test_get_i18n_ui_schema_with_sanitized_html():
    """Test get_i18n_ui_schema with SanitizedHTML field."""
    schema_class = get_i18n_ui_schema("lang", "value", "marshmallow_utils.fields.SanitizedHTML")

    assert schema_class is not None
    schema = schema_class()
    assert "lang" in schema.fields
    assert "value" in schema.fields
    assert isinstance(schema.fields["lang"], fields.String)
    # Check that the value field is the correct type (SanitizedHTML)
    assert schema.fields["value"].__class__.__name__ == "SanitizedHTML"


def test_get_i18n_ui_schema_caching():
    """Test that get_i18n_ui_schema properly caches results."""
    schema_class1 = get_i18n_ui_schema("lang", "value")
    schema_class2 = get_i18n_ui_schema("lang", "value")

    # Should return the same class instance due to caching
    assert schema_class1 is schema_class2

    # Different parameters should return different classes
    schema_class3 = get_i18n_ui_schema("language", "text")
    assert schema_class1 is not schema_class3


def test_get_i18n_ui_schema_invalid_field_class():
    """Test get_i18n_ui_schema with invalid field class."""
    with pytest.raises(ImportStringError):
        get_i18n_ui_schema("lang", "value", "nonexistent.field.Class")


def test_get_i18n_ui_schema_none_field_class():
    """Test get_i18n_ui_schema when obj_or_import_string returns None."""
    with pytest.raises(ValueError, match="Empty module name"):
        get_i18n_ui_schema("lang", "value", "")


def test_i18n_ui_schema_dumping():
    """Test dumping data with I18n UI schema."""
    schema_class = get_i18n_ui_schema("lang", "value", "marshmallow.fields.String")
    schema = schema_class()

    data = {"lang": "en", "value": "Hello World"}
    result = schema.dump(data)
    assert result == data


def test_i18n_ui_schema_dumping_with_html():
    """Test dumping data with SanitizedHTML field."""
    schema_class = get_i18n_ui_schema("lang", "value", "marshmallow_utils.fields.SanitizedHTML")
    schema = schema_class()

    data = {"lang": "en", "value": "<p>Hello <strong>World</strong></p>"}
    result = schema.dump(data)
    assert result == data


def test_multilingual_ui_field_basic():
    """Test basic MultilingualUIField functionality."""
    field = MultilingualUIField()

    assert isinstance(field, fields.List)
    assert isinstance(field.inner, fields.Nested)


def test_multilingual_ui_field_with_custom_params():
    """Test MultilingualUIField with custom parameters."""
    field = MultilingualUIField(
        lang_name="language",
        value_name="text",
        value_field="marshmallow.fields.String",
    )

    assert isinstance(field, fields.List)
    assert isinstance(field.inner, fields.Nested)


def test_multilingual_ui_field_with_args_ignored():
    """Test that args are ignored in MultilingualUIField."""
    field = MultilingualUIField(
        "ignored_arg1",
        "ignored_arg2",
        lang_name="lang",
        value_name="value",
        required=True,
    )

    assert isinstance(field, fields.List)
    assert field.required is True


def test_multilingual_ui_field_dumping():
    """Test dumping data with MultilingualUIField."""

    class TestSchema(Schema):
        multilingual = MultilingualUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    data = {
        "multilingual": [
            {"lang": "en", "value": "Hello"},
            {"lang": "cs", "value": "Ahoj"},
        ]
    }
    result = schema.dump(data)
    assert result == data


def test_multilingual_ui_field_empty_list():
    """Test MultilingualUIField with empty list."""

    class TestSchema(Schema):
        multilingual = MultilingualUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    data = {"multilingual": []}
    result = schema.dump(data)
    assert result == data


def test_multilingual_ui_field_with_html():
    """Test MultilingualUIField with SanitizedHTML field."""

    class TestSchema(Schema):
        multilingual = MultilingualUIField(
            lang_name="lang",
            value_name="content",
            value_field="marshmallow_utils.fields.SanitizedHTML",
        )

    schema = TestSchema()

    data = {
        "multilingual": [
            {"lang": "en", "content": "<p>Hello <em>World</em></p>"},
            {"lang": "cs", "content": "<p>Ahoj <em>světe</em></p>"},
        ]
    }
    result = schema.dump(data)
    assert result == data


def test_i18n_str_ui_field_basic():
    """Test basic I18nStrUIField functionality."""
    field = I18nStrUIField()

    assert isinstance(field, fields.Nested)


def test_i18n_str_ui_field_with_custom_params():
    """Test I18nStrUIField with custom parameters."""
    field = I18nStrUIField(
        lang_name="language",
        value_name="text",
        value_field="marshmallow.fields.String",
    )

    assert isinstance(field, fields.Nested)


def test_i18n_str_ui_field_with_args_and_kwargs():
    """Test I18nStrUIField passes args and kwargs correctly."""
    field = I18nStrUIField(
        required=True,
        allow_none=False,
        lang_name="lang",
        value_name="value",
        value_field="marshmallow.fields.String",
    )

    assert isinstance(field, fields.Nested)
    assert field.required is True
    assert field.allow_none is False


def test_i18n_str_ui_field_dumping():
    """Test dumping data with I18nStrUIField."""

    class TestSchema(Schema):
        title = I18nStrUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    data = {"title": {"lang": "en", "value": "Hello World"}}
    result = schema.dump(data)
    assert result == data


def test_i18n_str_ui_field_with_html():
    """Test I18nStrUIField with SanitizedHTML field."""

    class TestSchema(Schema):
        description = I18nStrUIField(
            lang_name="lang",
            value_name="content",
            value_field="marshmallow_utils.fields.SanitizedHTML",
        )

    schema = TestSchema()

    data = {"description": {"lang": "en", "content": "<p>Test <strong>content</strong></p>"}}
    result = schema.dump(data)
    assert result == data


def test_get_i18n_localized_ui_schema_basic():
    """Test get_i18n_localized_ui_schema basic functionality."""
    schema_class = get_i18n_localized_ui_schema("lang", "value")

    assert schema_class is not None
    assert issubclass(schema_class, Schema)
    assert schema_class.__name__ == "I18nLocalizedUISchema_lang_value"


def test_get_i18n_localized_ui_schema_custom_params():
    """Test get_i18n_localized_ui_schema with custom parameters."""
    schema_class = get_i18n_localized_ui_schema("language", "text")

    assert schema_class is not None
    assert issubclass(schema_class, Schema)
    assert schema_class.__name__ == "I18nLocalizedUISchema_language_text"


def test_get_i18n_localized_ui_schema_caching():
    """Test that get_i18n_localized_ui_schema properly caches results."""
    schema_class1 = get_i18n_localized_ui_schema("lang", "value")
    schema_class2 = get_i18n_localized_ui_schema("lang", "value")

    # Should return the same class instance due to caching
    assert schema_class1 is schema_class2

    # Different parameters should return different classes
    schema_class3 = get_i18n_localized_ui_schema("language", "text")
    assert schema_class1 is not schema_class3


def test_i18n_localized_ui_schema_serialize_empty():
    """Test localized schema serialization with empty data."""
    schema_class = get_i18n_localized_ui_schema("lang", "value")

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "en"
    schema = schema_class(context={"locale": mock_locale})

    result = schema.dump(None)
    assert result is None

    result = schema.dump([])
    assert result is None

    result = schema.dump("")
    assert result is None


def test_i18n_localized_ui_schema_serialize_with_matching_language():
    """Test localized schema serialization with matching language."""
    schema_class = get_i18n_localized_ui_schema("lang", "value")

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "en"
    schema = schema_class(context={"locale": mock_locale})

    data = [
        {"lang": "cs", "value": "Ahoj"},
        {"lang": "en", "value": "Hello"},
        {"lang": "de", "value": "Hallo"},
    ]

    result = schema.dump(data)
    assert result == "Hello"


def test_i18n_localized_ui_schema_serialize_without_matching_language():
    """Test localized schema serialization without matching language."""
    schema_class = get_i18n_localized_ui_schema("lang", "value")

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "fr"  # Language not in data
    schema = schema_class(context={"locale": mock_locale})

    data = [
        {"lang": "cs", "value": "Ahoj"},
        {"lang": "en", "value": "Hello"},
        {"lang": "de", "value": "Hallo"},
    ]

    result = schema.dump(data)
    # Should return the first item's value when no match is found
    assert result == "Ahoj"


def test_i18n_localized_ui_schema_serialize_single_item():
    """Test localized schema serialization with single item."""
    schema_class = get_i18n_localized_ui_schema("lang", "value")

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "fr"
    schema = schema_class(context={"locale": mock_locale})

    data = [{"lang": "en", "value": "Hello"}]

    result = schema.dump(data)
    assert result == "Hello"


def test_i18n_localized_ui_schema_serialize_custom_field_names():
    """Test localized schema serialization with custom field names."""
    schema_class = get_i18n_localized_ui_schema("language", "content")

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "cs"
    schema = schema_class(context={"locale": mock_locale})

    data = [
        {"language": "en", "content": "Hello"},
        {"language": "cs", "content": "Ahoj"},
    ]

    result = schema.dump(data)
    assert result == "Ahoj"


def test_multilingual_localized_ui_field_basic():
    """Test basic MultilingualLocalizedUIField functionality."""
    field = MultilingualLocalizedUIField()

    assert isinstance(field, fields.Nested)


def test_multilingual_localized_ui_field_with_custom_params():
    """Test MultilingualLocalizedUIField with custom parameters."""
    field = MultilingualLocalizedUIField(
        lang_name="language",
        value_name="text",
    )

    assert isinstance(field, fields.Nested)


def test_multilingual_localized_ui_field_with_args_and_kwargs():
    """Test MultilingualLocalizedUIField with args and kwargs."""
    field = MultilingualLocalizedUIField(
        required=True,
        allow_none=False,
        lang_name="lang",
        value_name="value",
    )

    assert isinstance(field, fields.Nested)
    assert field.required is True
    assert field.allow_none is False


def test_multilingual_localized_ui_field_dumping():
    """Test dumping data with MultilingualLocalizedUIField."""

    class TestSchema(Schema):
        localized_title = MultilingualLocalizedUIField(
            lang_name="lang",
            value_name="value",
        )

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "en"

    schema = TestSchema(context={"locale": mock_locale})

    data = {
        "localized_title": [
            {"lang": "cs", "value": "Český název"},
            {"lang": "en", "value": "English title"},
        ]
    }

    result = schema.dump(data)
    assert result == {"localized_title": "English title"}


def test_i18n_str_localized_ui_field_basic():
    """Test basic I18nStrLocalizedUIField functionality."""
    field = I18nStrLocalizedUIField()

    assert isinstance(field, fields.Nested)


def test_i18n_str_localized_ui_field_with_custom_params():
    """Test I18nStrLocalizedUIField with custom parameters."""
    field = I18nStrLocalizedUIField(
        lang_name="language",
        value_name="text",
    )

    assert isinstance(field, fields.Nested)


def test_i18n_str_localized_ui_field_args_ignored():
    """Test that args are ignored in I18nStrLocalizedUIField."""
    field = I18nStrLocalizedUIField(
        "ignored_arg1",
        "ignored_arg2",
        required=True,
        lang_name="lang",
        value_name="value",
    )

    assert isinstance(field, fields.Nested)
    assert field.required is True


def test_i18n_str_localized_ui_field_dumping():
    """Test dumping data with I18nStrLocalizedUIField."""

    class TestSchema(Schema):
        title = I18nStrLocalizedUIField(
            lang_name="lang",
            value_name="value",
        )

    schema = TestSchema()

    data = {"title": {"lang": "en", "value": "Hello World"}}
    result = schema.dump(data)
    assert result == data


def test_schema_with_multiple_ui_fields():
    """Test schema with multiple UI fields."""

    class DocumentUISchema(Schema):
        title = I18nStrUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )
        descriptions = MultilingualUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow_utils.fields.SanitizedHTML",
        )
        localized_summary = MultilingualLocalizedUIField(
            lang_name="lang",
            value_name="value",
        )

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "en"

    schema = DocumentUISchema(context={"locale": mock_locale})

    data = {
        "title": {"lang": "en", "value": "Document Title"},
        "descriptions": [
            {"lang": "en", "value": "<p>English description</p>"},
            {"lang": "cs", "value": "<p>Český popis</p>"},
        ],
        "localized_summary": [
            {"lang": "en", "value": "Summary in English"},
            {"lang": "cs", "value": "Souhrn v češtině"},
        ],
    }

    result = schema.dump(data)
    expected = {
        "title": {"lang": "en", "value": "Document Title"},
        "descriptions": [
            {"lang": "en", "value": "<p>English description</p>"},
            {"lang": "cs", "value": "<p>Český popis</p>"},
        ],
        "localized_summary": "Summary in English",
    }
    assert result == expected


def test_complex_nested_ui_scenario():
    """Test complex nested scenario with various UI field types."""

    class ComplexUISchema(Schema):
        simple_title = I18nStrUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )
        alternative_titles = MultilingualUIField(
            lang_name="language",
            value_name="text",
            value_field="marshmallow_utils.fields.SanitizedHTML",
        )
        localized_subtitle = I18nStrLocalizedUIField(
            lang_name="lang",
            value_name="content",
        )
        metadata = fields.Dict()

    # Mock locale context
    mock_locale = Mock()
    mock_locale.language = "de"

    schema = ComplexUISchema(context={"locale": mock_locale})

    complex_data = {
        "simple_title": {"lang": "en", "value": "Main Title"},
        "alternative_titles": [
            {"language": "en", "text": "<p>Alternative English Title</p>"},
            {"language": "de", "text": "<p>Deutscher Alternativtitel</p>"},
        ],
        "localized_subtitle": {"lang": "de", "content": "Deutscher Untertitel"},
        "metadata": {"author": "Test Author"},
    }

    result = schema.dump(complex_data)
    expected = {
        "simple_title": {"lang": "en", "value": "Main Title"},
        "alternative_titles": [
            {"language": "en", "text": "<p>Alternative English Title</p>"},
            {"language": "de", "text": "<p>Deutscher Alternativtitel</p>"},
        ],
        "localized_subtitle": {"lang": "de", "content": "Deutscher Untertitel"},
        "metadata": {"author": "Test Author"},
    }
    assert result == expected


@pytest.mark.parametrize(
    ("field_class", "expected_field_name"),
    [
        ("marshmallow.fields.String", "String"),
        ("marshmallow.fields.Integer", "Integer"),
        ("marshmallow_utils.fields.SanitizedHTML", "SanitizedHTML"),
        ("marshmallow_utils.fields.SanitizedUnicode", "SanitizedUnicode"),
    ],
)
def test_different_value_field_types(field_class, expected_field_name):
    """Test schema creation with different value field types."""
    schema_class = get_i18n_ui_schema("lang", "value", field_class)
    schema = schema_class()

    assert "lang" in schema.fields
    assert "value" in schema.fields
    assert isinstance(schema.fields["lang"], fields.String)
    assert schema.fields["value"].__class__.__name__ == expected_field_name


def test_field_parameters_edge_cases():
    """Test edge cases for field parameters."""
    # Test with very long field names
    schema_class = get_i18n_ui_schema(
        "very_long_language_field_name",
        "very_long_value_field_name",
        "marshmallow.fields.String",
    )
    schema = schema_class()

    assert "very_long_language_field_name" in schema.fields
    assert "very_long_value_field_name" in schema.fields

    # Test with special characters in field names (valid Python identifiers)
    schema_class2 = get_i18n_ui_schema("lang_", "value_", "marshmallow.fields.String")
    schema2 = schema_class2()

    assert "lang_" in schema2.fields
    assert "value_" in schema2.fields


def test_serialization_with_none_values():
    """Test serialization behavior with None values."""

    class TestSchema(Schema):
        title = I18nStrUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )
        descriptions = MultilingualUIField(
            lang_name="lang",
            value_name="value",
            value_field="marshmallow.fields.String",
        )

    schema = TestSchema()

    data = {
        "title": None,
        "descriptions": None,
    }

    result = schema.dump(data)
    assert result == {"title": None, "descriptions": None}


def test_localized_schema_edge_cases():
    """Test edge cases for localized schema serialization."""
    schema_class = get_i18n_localized_ui_schema("lang", "value")

    # Test with missing locale context
    schema_no_context = schema_class()

    data = [{"lang": "en", "value": "Hello"}]

    # This should raise an error because locale is not in context
    with pytest.raises((KeyError, AttributeError)):
        schema_no_context.dump(data)

    # Test with locale context but invalid locale object
    mock_locale = Mock()
    mock_locale.language = None
    schema_invalid_locale = schema_class(context={"locale": mock_locale})

    result = schema_invalid_locale.dump(data)
    # Should still return first item when locale.language is None
    assert result == "Hello"


def test_many_parameter_ignored():
    """Test that the localized schema works correctly with dump method."""
    schema_class = get_i18n_localized_ui_schema("lang", "value")

    mock_locale = Mock()
    mock_locale.language = "en"
    schema = schema_class(context={"locale": mock_locale})

    data = [{"lang": "en", "value": "Hello"}]

    # Test normal dump behavior
    result = schema.dump(data)
    assert result == "Hello"
