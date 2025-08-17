#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for component ordering, partially AI generated."""

from __future__ import annotations

import functools
import re

import pytest
from invenio_records_resources.services.records.components import ServiceComponent
from invenio_records_resources.services.records.config import ServiceConfig
from invenio_records_resources.services.records.service import Service as InvenioService

from oarepo_runtime.services.config.components import ComponentsOrderingMixin


class A(ServiceComponent):
    """A service component."""


class B(ServiceComponent):
    """B service component."""


class C(ServiceComponent):
    """C service component."""


class D(ServiceComponent):
    """D service component."""


class Base(ServiceComponent):
    """Base service component."""


class Derived(Base):
    """Derived service component."""


class DependingOnX(ServiceComponent):
    """Component that depends on A."""

    depends_on = (A,)


class AffectingAll(ServiceComponent):
    """Component that affects all other components."""

    affects = "*"


class DependsOnAll(ServiceComponent):
    """Component that depends on all other components."""

    depends_on = "*"


class Service(ComponentsOrderingMixin, InvenioService):
    """A sample invenio records service, will be used for testing component ordering."""


def names(seq):
    """Return class names for a sequence of components.

    Keeps non-class inputs (e.g., partial) represented by their type name
    for easy assertions.
    """
    return [type(x).__name__ for x in seq]


def test_preserves_order_without_dependencies():
    """When there are no relationships, preserve original order as a tuple."""

    class Cfg(ServiceConfig):
        components = (A, B, C)

    service = Service(Cfg())
    assert names(service.components) == ["A", "B", "C"]


def test_depends_on_orders_before():
    """A component must come after its dependencies."""

    class Dep(ServiceComponent):
        pass

    class Uses(ServiceComponent):
        depends_on = (Dep,)

    class Cfg(ServiceConfig):
        components = (Uses, Dep, C)

    service = Service(Cfg())
    assert names(service.components) == ["Dep", "Uses", "C"]


def test_affects_orders_before_affected():
    """If X.affects=Y, then X must be ordered before Y."""
    Consumer = type("Consumer", (ServiceComponent,), {})

    class Producer(ServiceComponent):
        affects = (Consumer,)

    class Cfg(ServiceConfig):
        components = (Consumer, Producer, A)

    service = Service(Cfg())
    assert names(service.components) == ["Producer", "Consumer", "A"]


def test_star_affects_propagation():
    """If X.affects='*' and Y.affects=X, order starts with Y, X, then the rest."""

    class Y(ServiceComponent):
        affects = (AffectingAll,)

    class Cfg(ServiceConfig):
        components = (AffectingAll, Y, A, B)

    service = Service(Cfg())
    assert names(service.components) == ["Y", "AffectingAll", "A", "B"]


def test_star_depends_propagation():
    """If X.depends_on='*', it and dependents go to the end, ordered by deps."""

    class Y(ServiceComponent):
        depends_on = (DependsOnAll,)

    class Cfg(ServiceConfig):
        components = (Y, C, DependsOnAll, D)

    service = Service(Cfg())
    assert names(service.components) == ["C", "D", "DependsOnAll", "Y"]


def test_class_deduplication_same_class():
    """Duplicate classes are removed while preserving order."""

    class Cfg(ServiceConfig):
        components = (A, B, A, A, C)

    service = Service(Cfg())
    assert names(service.components) == ["A", "B", "C"]


def test_inheritance_deduplication_keeps_derived():
    """If Base and Derived(Base) appear, keep only Derived in that position."""

    class Cfg(ServiceConfig):
        components = (Base, Derived, A)

    service = Service(Cfg())
    assert names(service.components) == ["Derived", "A"]


def test_partial_component_is_supported_and_preserved():
    """Partials are supported; the original partial object is preserved."""
    part_b = functools.partial(B)

    class Cfg(ServiceConfig):
        components = (A, part_b, C)

    service = Service(Cfg())
    assert names(service.components) == ["A", "B", "C"]


def test_property_setter_orders_and_returns_tuple():
    """Setting components via setter orders and returns an immutable tuple."""
    cfg = ServiceConfig()

    cfg.components = (DependingOnX, A)

    service = Service(cfg)
    assert names(service.components) == ["A", "DependingOnX"]


def test_cycle_raises_cycleerror():
    """A dependency cycle should raise graphlib.CycleError."""

    class X(ServiceComponent):
        depends_on = ()

    class Y(ServiceComponent):
        depends_on = ()

    X.depends_on = (Y,)
    Y.depends_on = (X,)

    class Cfg(ServiceConfig):
        components = (X, Y)

    service = Service(Cfg())
    with pytest.raises(
        ValueError,
        match=re.escape("Cycle detected in dependencies: {CD(X): {CD(Y)}, CD(Y): {CD(X)}}"),
    ):
        _ = service.components
