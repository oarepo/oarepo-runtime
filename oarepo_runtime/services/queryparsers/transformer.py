#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Transformers for query parsing."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from luqum.tree import Phrase
from luqum.visitor import TreeTransformer

if TYPE_CHECKING:
    from collections.abc import Generator

    from luqum.tree import Term, Word

ILLEGAL_ELASTICSEARCH_CHARACTERS = {
    "\\",
    "/",
    "+",
    "&&",
    "||",
    "!",
    "(",
    ")",
    "{",
    "}",
    "[",
    "]",
    "^",
    '"',
    "~",
    "*",
    "?",
    ":",
}
ILLEGAL_START_ELASTICSEARCH_CHARACTERS = {"-"}
ILLEGAL_ELASTICSEARCH_CHARACTERS_REGEX = r'[\\\/\+\!\(\)\{\}\[\]\^"~\*\?:]|&&|\|\|'
ILLEGAL_START_ELASTICSEARCH_CHARACTERS_REGEX = r"^\-"


class SearchQueryValidator(TreeTransformer):
    """Validate search terms for illegal Elasticsearch characters."""

    def __init__(self, mapping: Any, allow_list: Any, *args: Any, **kwargs: Any):
        """Initialize the transformer."""
        _, _ = mapping, allow_list  # currently unused
        super().__init__(*args, **kwargs)

    def visit_word(self, node: Word, context: Any) -> Generator[Term]:
        """Visit a word term."""
        # unused context here but keeping the signature required by luqum visitor
        _ = context

        # convert to phrase if the value contains an illegal elasticsearch character
        if re.search(ILLEGAL_ELASTICSEARCH_CHARACTERS_REGEX, node.value):
            val = node.value.replace('"', r"\"")
            yield Phrase(f'"{val}"')
            return

        # some characters are ok if they are not at the start of the term,
        # for example '-' is ok in 'e-mail' but not at the start as -mail
        if re.search(ILLEGAL_START_ELASTICSEARCH_CHARACTERS_REGEX, node.value):
            val = node.value.replace('"', r"\"")
            yield Phrase(f'"{val}"')
            return

        yield node
