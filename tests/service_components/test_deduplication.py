# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

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

    replaces = (A,)


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
        replaces = (A, B)

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


def test_skipped_and_removed():
    class D(B):
        replaces = (B,)

    cfg = DummyConfig()
    res = cfg._deduplicate_components([D, B, D, B, D])  # noqa: SLF001
    assert comp_classes(res) == [D]
    res = cfg._deduplicate_components([B, D, B, D, B])  # noqa: SLF001
    assert comp_classes(res) == [D]


def test_deduplication_replaced_by_scenario():
    """Test when existing component is in new_component.replaced_by.

    This covers line 511 where we return 'skip'.

    For line 511 to trigger: existing.component_class in new.replaced_by
    Meaning the new component says "I am replaced by" something already in data.
    """

    class Replacer(ServiceComponent):
        pass

    class ToBeReplaced(ServiceComponent):
        # ToBeReplaced says it's replaced by Replacer
        replaced_by = (Replacer,)

    cfg = DummyConfig()
    # Add Replacer first, then ToBeReplaced
    # When processing ToBeReplaced (new), Replacer (existing) is checked:
    #   _deduplication_action(ToBeReplaced, Replacer):
    #   Is Replacer in ToBeReplaced.replaced_by? Yes -> return "skip" (line 511)
    res = cfg._deduplicate_components([Replacer, ToBeReplaced])  # noqa: SLF001
    assert comp_classes(res) == [Replacer]  # ToBeReplaced is skipped


def test_deduplication_ok_scenario():
    """Test when components are independent and both kept (ok action)."""

    class X(ServiceComponent):
        pass

    class Y(ServiceComponent):
        pass

    cfg = DummyConfig()
    res = cfg._deduplicate_components([X, Y])  # noqa: SLF001
    assert comp_classes(res) == [X, Y]


def test_remove_indices_from_data():
    """Test _remove_indices_from_data helper method."""

    class X(ServiceComponent):
        pass

    class Y(ServiceComponent):
        pass

    class Z(ServiceComponent):
        pass

    cfg = DummyConfig()
    data = cfg._deduplicate_components([X, Y, Z])  # noqa: SLF001

    # Remove indices [0, 2] (X and Z), keeping only Y
    cfg._remove_indices_from_data(data, [0, 2])  # noqa: SLF001
    assert len(data) == 1
    assert data[0].component_class is Y


def test_deduplication_skip_with_replaces_same_time():
    """Test case where skipped=True and replaced_indices is non-empty.

    This covers line 478 which the comment says 'probably never happens'.

    Setup:
    - Data starts with [A, B] where A.replaced_by=(C,) and B.replaces=(C,)
    - When adding C:
      - vs A: C in A.replaced_by -> "replace" (A gets replaced by C)
      - vs B: C in B.replaces -> "skip" (B says it replaces C, so skip C)
    - Result: skipped=True with replaced_indices=[0], triggering line 478
    """

    class A(ServiceComponent):
        replaced_by = ()  # Will be set below to avoid forward reference issues

    class B(ServiceComponent):
        replaces = ()  # Will be set below

    class C(ServiceComponent):
        pass

    # Set up relationships after class definition
    A.replaced_by = (C,)  # A is replaced by C
    B.replaces = (C,)  # B replaces C

    cfg = DummyConfig()
    # Data has [A, B]
    # Add C which triggers both skip (from B) and replace (of A)
    res = cfg._deduplicate_components([A, B, C])  # noqa: SLF001
    # C would replace A, but C is skipped due to B
    # So B stays, A is removed (line 478 removes the replaced index)
    assert comp_classes(res) == [B]
