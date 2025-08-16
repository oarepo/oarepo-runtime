#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Tests for the dependency propagation, partially AI generated."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_runtime.services.config.components import (
    ComponentData,
    ComponentsOrderingMixin,
)

if TYPE_CHECKING:
    from invenio_records_resources.services.records.service import RecordService


mock_service = cast("RecordService", object())  # Mock service object for testing


class _DummyConfig(ComponentsOrderingMixin):
    """Minimal config to call protected helpers without pulling full stack."""

    def __init__(self):  # do not call super().__init__
        self._ordered_components = None

    # public wrapper for testing the internal propagation logic
    def propagate(
        self,
        selected,
        potentials,
        selected_dependency_getter,
        potential_dependency_getter,
    ) -> None:
        return self._propagate_dependencies(
            selected,
            potentials,
            selected_dependency_getter,
            potential_dependency_getter,
        )


def _cd(component_cls: type[ServiceComponent]) -> ComponentData:
    """Return ComponentData constructed from a component class."""
    return ComponentData(original_component=component_cls, service=mock_service)


def test_propagate_from_selected_depends_on_adds_needed_potentials():
    # A depends on B -> if A is selected and B is in potentials, B gets added
    class A(ServiceComponent):
        pass

    class B(ServiceComponent):
        pass

    class C(ServiceComponent):
        pass

    # set relationships after definitions to avoid forward-ref issues
    A.depends_on = [B]
    A.affects = []
    B.depends_on = []
    B.affects = []
    C.depends_on = []
    C.affects = []

    cfg = _DummyConfig()
    selected = [_cd(A)]
    potentials = [_cd(B), _cd(C)]

    cfg.propagate(
        selected,
        potentials,
        selected_dependency_getter=lambda x: x.depends_on,
        potential_dependency_getter=lambda x: x.affects,
    )

    assert {_c.component_class for _c in selected} == {A, B}


def test_propagate_from_potentials_affects_selected_adds_them():
    # If B.affects A and A is selected, B gets added from potentials
    class A(ServiceComponent):
        pass

    class B(ServiceComponent):
        pass

    A.depends_on = []
    A.affects = []
    B.depends_on = []
    B.affects = [A]

    cfg = _DummyConfig()
    selected = [_cd(A)]
    potentials = [_cd(B)]

    cfg.propagate(
        selected,
        potentials,
        selected_dependency_getter=lambda x: x.depends_on,
        potential_dependency_getter=lambda x: x.affects,
    )

    assert {_c.component_class for _c in selected} == {A, B}


def test_propagate_transitive_dependencies():
    # A depends on B, B depends on C -> selecting A brings in B and then C
    class A(ServiceComponent):
        pass

    class B(ServiceComponent):
        pass

    class C(ServiceComponent):
        pass

    A.depends_on = [B]
    A.affects = []
    B.depends_on = [C]
    B.affects = []
    C.depends_on = []
    C.affects = []

    cfg = _DummyConfig()
    selected = [_cd(A)]
    potentials = [_cd(B), _cd(C)]

    cfg.propagate(
        selected,
        potentials,
        selected_dependency_getter=lambda x: x.depends_on,
        potential_dependency_getter=lambda x: x.affects,
    )

    assert {_c.component_class for _c in selected} == {A, B, C}


def test_propagate_matches_on_mro_subclassing():
    # A depends on BaseB; SubB is a subclass of BaseB -> SubB should be added
    class A(ServiceComponent):
        pass

    class BaseB(ServiceComponent):
        pass

    class SubB(BaseB):
        pass

    A.depends_on = [BaseB]
    A.affects = []
    BaseB.depends_on = []
    BaseB.affects = []
    SubB.depends_on = []
    SubB.affects = []

    cfg = _DummyConfig()
    selected = [_cd(A)]
    potentials = [_cd(SubB)]

    cfg.propagate(
        selected,
        potentials,
        selected_dependency_getter=lambda x: x.depends_on,
        potential_dependency_getter=lambda x: x.affects,
    )

    assert {_c.component_class for _c in selected} == {A, SubB}


def test_propagate_for_depends_on_all_semantics():
    """Using (selected.affects, potentials.depends_on) adds affect- and depend-based matches."""

    class A(ServiceComponent):
        pass

    class B(ServiceComponent):
        pass

    class D(ServiceComponent):
        pass

    A.depends_on = []
    A.affects = [B]
    B.depends_on = []
    B.affects = []
    D.depends_on = [A]
    D.affects = []

    cfg = _DummyConfig()
    selected = [_cd(A)]
    potentials = [_cd(B), _cd(D)]

    cfg.propagate(
        selected,
        potentials,
        selected_dependency_getter=lambda x: x.affects,
        potential_dependency_getter=lambda x: x.depends_on,
    )

    assert {_c.component_class for _c in selected} == {A, B, D}


def test_propagate_no_changes_when_no_relationships():
    class A(ServiceComponent):
        pass

    class B(ServiceComponent):
        pass

    A.depends_on = []
    A.affects = []
    B.depends_on = []
    B.affects = []

    cfg = _DummyConfig()
    selected = [_cd(A)]
    potentials = [_cd(B)]

    cfg.propagate(
        selected,
        potentials,
        selected_dependency_getter=lambda x: x.depends_on,
        potential_dependency_getter=lambda x: x.affects,
    )

    # unchanged
    assert {_c.component_class for _c in selected} == {A}
