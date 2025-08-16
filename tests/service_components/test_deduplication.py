#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Tests for the ComponentData class, partially AI generated."""

from __future__ import annotations

from functools import partial

import pytest
from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_runtime.services.config.components import ComponentsOrderingMixin


class DummyConfig(ComponentsOrderingMixin):
    """Minimal config to access the mixin internals."""


class A(ServiceComponent):
    """Base component A for tests."""


class B(A):
    """Subclass of A for tests."""


class C(ServiceComponent):
    """Independent component C for tests."""


def comp_classes(result):
    """Return component classes from _deduplicate_components result."""
    return [cd.component_class for cd in result]


def test_class_deduplication_keeps_single_instance_and_order():
    cfg = DummyConfig()
    res = cfg._deduplicate_components([A, C, A])  # noqa: SLF001
    assert comp_classes(res) == [A, C]


def test_inheritance_deduplication_keeps_subclass_once():
    cfg = DummyConfig()
    res = cfg._deduplicate_components([A, B])  # noqa: SLF001
    assert comp_classes(res) == [B]


def test_inheritance_multi_level_only_most_specific_kept_and_order_preserved():
    class D(B):
        pass

    cfg = DummyConfig()
    res = cfg._deduplicate_components([A, C, B, D])  # noqa: SLF001
    # as D is a subclass of both A and B, it replaces A
    assert comp_classes(res) == [D, C]


def test_mixed_class_and_partial_are_deduplicated():
    cfg = DummyConfig()
    pB = partial(B)
    res = cfg._deduplicate_components([A, pB, B, C])  # noqa: SLF001
    assert comp_classes(res) == [B, C]


def test_invalid_component_raises_typeerror():
    cfg = DummyConfig()

    class NotAComponent:
        pass

    with pytest.raises(TypeError):
        cfg._deduplicate_components([NotAComponent])  # noqa: SLF001
