# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Tests for the topological graph."""

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


def _graph_to_class_map(
    graph: dict[ComponentData, set[ComponentData]],
) -> dict[type, set[type]]:
    """Convert a ComponentData graph to a class->set[class] mapping for asserts."""
    return {k.component_class: {v.component_class for v in deps} for k, deps in graph.items()}


class A(ServiceComponent):
    """Base component A."""


class BDependsOnA(ServiceComponent):
    """Component B that depends on A."""

    depends_on = (A,)


class CAffectsA(ServiceComponent):
    """Component C that affects A."""

    affects = (A,)


class ASub(A):
    """A subclass of A."""


class TestService(ComponentsOrderingMixin):
    """Helper config exposing graph creation for tests."""

    def __init__(self, config: None = None):
        """Construct Dummy service."""

    def create(self, items: list[ComponentData]) -> dict[ComponentData, set[ComponentData]]:
        """Create the topo graph for given ComponentData list (test helper)."""
        return self._create_topo_graph(items)


def test_create_topo_graph_depends_on_edge_direction():
    """If B depends_on A, the graph should read B->A, A->{}."""
    comps = [
        ComponentData(A, service=mock_service),
        ComponentData(BDependsOnA, service=mock_service),
    ]
    graph = TestService(None).create(comps)
    m = _graph_to_class_map(graph)

    # Doc: If A is in B.depends_on, the graph will contain A in B's set.
    assert m[A] == set()
    assert m[BDependsOnA] == {A}


def test_create_topo_graph_affects_adds_reverse_dependency():
    """If C affects A, the graph adds A->C, C->{}."""
    comps = [
        ComponentData(A, service=mock_service),
        ComponentData(CAffectsA, service=mock_service),
    ]
    graph = TestService(None).create(comps)
    m = _graph_to_class_map(graph)

    # Doc: If A is in C.affects, the graph will contain C in A's dependencies.
    assert m[CAffectsA] == set()
    assert m[A] == {CAffectsA}


def test_create_topo_graph_matches_via_inheritance_for_depends_on():
    """Depends_on matches subclasses via MRO membership.

    If B depends on base A and only ASub is present, the graph adds
    B->ASub and ASub->{}.
    """
    comps = [
        ComponentData(ASub, service=mock_service),
        ComponentData(BDependsOnA, service=mock_service),
    ]
    graph = TestService(None).create(comps)
    m = _graph_to_class_map(graph)

    # Doc + inheritance: ASub stands in for A, so B's dependencies contains ASub.
    assert m[ASub] == set()
    assert m[BDependsOnA] == {ASub}


def test_create_topo_graph_matches_via_inheritance_for_affects():
    """Affects matches subclasses via MRO membership.

    If C affects base A and only ASub is present, the graph adds
    ASub -> C and C -> {}.
    """
    comps = [
        ComponentData(ASub, service=mock_service),
        ComponentData(CAffectsA, service=mock_service),
    ]
    graph = TestService(None).create(comps)
    m = _graph_to_class_map(graph)

    # Doc + inheritance: ASub stands in for A, A's dependencies must include CAffectsA.
    assert m[CAffectsA] == set()
    assert m[ASub] == {CAffectsA}


def test_create_topo_graph_ignores_non_present_dependencies():
    """No edges are added for dependencies not present in the list."""

    class X(ServiceComponent):
        pass

    class BDependsOnX(ServiceComponent):
        """Component depending on X (which is not present)."""

        depends_on = (X,)

    comps = [
        ComponentData(A, service=mock_service),
        ComponentData(BDependsOnX, service=mock_service),
    ]
    graph = TestService(None).create(comps)
    m = _graph_to_class_map(graph)

    # X is not present, so B has no concrete dependency edge.
    assert m[A] == set()
    assert m[BDependsOnX] == set()


def test_topo_sort_with_multiple_zero_indegree_items():
    """Test topo sort when multiple items have indegree 0 after decrementing.

    This covers line 315->313 where v.indeg becomes 0 and is pushed to heap.
    """

    class A(ServiceComponent):
        pass

    class B(ServiceComponent):
        depends_on = (A,)

    class C(ServiceComponent):
        depends_on = (A,)

    class D(ServiceComponent):
        depends_on = (B, C)

    cfg = TestService(None)
    comps = [
        ComponentData(A, service=mock_service),
        ComponentData(B, service=mock_service),
        ComponentData(C, service=mock_service),
        ComponentData(D, service=mock_service),
    ]

    result = cfg._topo_sort(comps)
    result_classes = [c.component_class for c in result]

    # A must come first, then B and C (order between them preserved by input order),
    # then D
    assert result_classes[0] is A
    assert D in result_classes
    assert result_classes.index(D) > result_classes.index(B)
    assert result_classes.index(D) > result_classes.index(C)


def test_get_dependencies_from_potentials_matches_via_mro():
    """Test _get_dependencies_from_potentials with MRO matching.

    Covers line 438->437 where the condition matches.

    The logic: if p.affects contains something in s.component_mro, add p.
    """

    class BaseService(ServiceComponent):
        pass

    class Consumer(BaseService):
        # Consumer is a subclass of BaseService
        pass

    class AffectsBase(ServiceComponent):
        affects = (BaseService,)

    cfg = TestService(None)
    # Consumer is selected (it's a BaseService subclass)
    selected = [ComponentData(Consumer, service=mock_service)]
    # AffectsBase affects BaseService, and Consumer is in BaseService's MRO
    potentials = [ComponentData(AffectsBase, service=mock_service)]

    result = cfg._get_dependencies_from_potentials(
        selected,
        potentials,
        potential_dependency_getter=lambda x: x.affects,
    )

    assert 0 in result  # AffectsBase should be added
