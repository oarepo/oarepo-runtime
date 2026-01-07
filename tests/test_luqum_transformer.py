#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Tests for luqum transformer."""

from __future__ import annotations

import pytest
from invenio_records_resources.services.errors import QuerystringValidationError
from luqum.tree import Word

from oarepo_runtime.services.queryparsers.transformer import (
    ILLEGAL_ELASTICSEARCH_CHARACTERS,
    ILLEGAL_START_ELASTICSEARCH_CHARACTERS,
    SearchQueryValidator,
)

# Convert to list for parametrize
ILLEGAL_CHARS_LIST = list(ILLEGAL_ELASTICSEARCH_CHARACTERS)


@pytest.fixture(scope="module")
def transformer():
    """Fixture for SearchQueryValidator."""
    return SearchQueryValidator(None, None)


@pytest.mark.parametrize(
    "illegal_char",
    ILLEGAL_CHARS_LIST + list(ILLEGAL_START_ELASTICSEARCH_CHARACTERS),
)
def test_word_with_illegal_character_at_start(illegal_char, transformer):
    """Test words starting with illegal characters raise error."""
    word = Word(f"{illegal_char}test")

    with pytest.raises(QuerystringValidationError) as exc_info:
        list(transformer.visit_word(word, context=None))

    assert "Illegal character in search term" in str(exc_info.value)


@pytest.mark.parametrize("illegal_char", ILLEGAL_CHARS_LIST)
def test_word_with_illegal_character_at_end(illegal_char, transformer):
    """Test words ending with illegal characters raise error."""
    word = Word(f"test{illegal_char}")

    with pytest.raises(QuerystringValidationError) as exc_info:
        list(transformer.visit_word(word, context=None))

    assert "Illegal character in search term" in str(exc_info.value)


@pytest.mark.parametrize("illegal_char", ILLEGAL_CHARS_LIST)
def test_word_with_illegal_character_in_middle(illegal_char, transformer):
    """Test words with illegal characters in the middle raise error."""
    word = Word(f"te{illegal_char}st")

    with pytest.raises(QuerystringValidationError) as exc_info:
        list(transformer.visit_word(word, context=None))

    assert "Illegal character in search term" in str(exc_info.value)


@pytest.mark.parametrize(
    "test_word",
    [
        "simple",
        "test123",
        "CamelCase",
        "with_underscore",
        "with.dot",
        "with@at",
        "with#hash",
        "with$dollar",
        "with%percent",
        "with&single_ampersand",
        "with|single_pipe",
        "test_value_123",
        "αβγ",  # Greek letters
        "测试",  # Chinese characters
    ],
)
def test_word_without_illegal_characters_yields_node(test_word, transformer):
    """Test words without illegal characters yield the node."""
    word = Word(test_word)

    result = list(transformer.visit_word(word, context=None))

    assert len(result) == 1
    assert result[0] == word


def test_word_with_multiple_illegal_characters(transformer):
    """Test words with multiple illegal characters raise error."""
    word = Word("test+value{123")

    with pytest.raises(QuerystringValidationError) as exc_info:
        list(transformer.visit_word(word, context=None))

    assert "Illegal character in search term" in str(exc_info.value)


@pytest.mark.parametrize(
    ("value", "expected_contains_illegal"),
    [(f"{char}test", True) for char in ILLEGAL_CHARS_LIST]
    + [
        ("test", False),
        ("test123", False),
        ("test_value", False),
        ("test.value", False),
    ],
)
def test_matrix_illegal_vs_legal_characters(value, expected_contains_illegal, transformer):
    """Matrix test for all character combinations."""
    word = Word(value)

    if expected_contains_illegal:
        # Should raise error
        with pytest.raises(QuerystringValidationError) as exc_info:
            list(transformer.visit_word(word, context=None))
        assert "Illegal character in search term" in str(exc_info.value)
    else:
        # Should yield the node
        result = list(transformer.visit_word(word, context=None))
        assert len(result) == 1
        assert result[0] == word


def test_empty_string_yields_node(transformer):
    """Test empty string yields node (no illegal chars)."""
    word = Word("")

    result = list(transformer.visit_word(word, context=None))
    assert len(result) == 1
    assert result[0] == word
