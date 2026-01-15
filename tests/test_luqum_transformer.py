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
from luqum.auto_head_tail import auto_head_tail
from luqum.parser import parser
from luqum.tree import Phrase, Word

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
    tested_str = f"{illegal_char}test"
    word = Word(tested_str)

    phrase_word = '"\\"test"' if illegal_char == '"' else f'"{tested_str}"'
    assert list(transformer.visit_word(word, context=None)) == [Phrase(phrase_word)]


@pytest.mark.parametrize("illegal_char", ILLEGAL_CHARS_LIST)
def test_word_with_illegal_character_at_end(illegal_char, transformer):
    """Test words ending with illegal characters raise error."""
    tested_str = f"test{illegal_char}"

    word = Word(tested_str)

    phrase_word = '"test\\""' if illegal_char == '"' else f'"{tested_str}"'
    assert list(transformer.visit_word(word, context=None)) == [Phrase(phrase_word)]


@pytest.mark.parametrize("illegal_char", ILLEGAL_CHARS_LIST)
def test_word_with_illegal_character_in_middle(illegal_char, transformer):
    """Test words with illegal characters in the middle raise error."""
    tested_str = f"te{illegal_char}st"

    word = Word(tested_str)

    phrase_word = '"te\\"st"' if illegal_char == '"' else f'"{tested_str}"'
    assert list(transformer.visit_word(word, context=None)) == [Phrase(phrase_word)]


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

    assert list(transformer.visit_word(word, context=None)) == [Phrase('"test+value{123"')]


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
        assert list(transformer.visit_word(word, context=None)) == [Phrase(f'"{value.replace('"', '\\"')}"')]
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


def visit(query):
    parsed = parser.parse(query)
    transformed_tree = SearchQueryValidator(None, None).visit(parsed, context=None)
    transformed_tree = auto_head_tail(transformed_tree)
    return str(transformed_tree)


def test_visit():
    query = "lalala tralala"
    assert visit(query) == "lalala tralala"


def test_url_edge_cases():
    urls = [
        "https://doi.org/10.5281/zenodo.18184329",
        "doi:10.5281/zenodo.18184329",
        "handle:11372/LRT-707",
        "https://127.0.0.1:5000/s/doi/10.5281/zenodo.18184329",
        "oai:https://127.0.0.1:5000:doi/10.5281/zenodo.18184329",
    ]

    for url in urls:
        assert visit(url) == f'"{url}"'


def test_multi_word_query_with_url():
    """Test empty string yields node (no illegal chars)."""
    query = "lalala tralala https://doi.org/10.5281/zenodo.18184329 falala"

    result = 'lalala tralala "https://doi.org/10.5281/zenodo.18184329" falala'

    assert visit(query) == result


def test_more_urls(transformer):
    query = "lalala http://www.tralala.fyi http://doi.org/10.5281/zenodo.18184329 doi:10.5281/zenodo.18184329 falala"

    result = (
        'lalala "http://www.tralala.fyi" "http://doi.org/10.5281/zenodo.18184329" "doi:10.5281/zenodo.18184329" falala'
    )

    assert visit(query) == result


def test_cut_http(transformer):
    query1 = "http:// www.tralala.fyi"
    query2 = "http://www.tralala.fyi"

    result = '"http://" www.tralala.fyi'
    result2 = '"http://www.tralala.fyi"'

    assert visit(query1) == result
    assert visit(query2) == result2
