#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for typed permission generators wrappers.

We verify that our wrappers delegate to Invenio base classes and keep behavior.
"""

from __future__ import annotations

from typing import Any

from flask_principal import Need
from invenio_records_permissions.generators import (
    ConditionalGenerator as InvenioConditionalGenerator,
)
from invenio_records_permissions.generators import Generator as InvenioGenerator
from invenio_search.engine import dsl

from oarepo_runtime.services.generators import ConditionalGenerator, Generator


def test_generator_delegates_methods(monkeypatch):
    """Generator methods should delegate to Invenio base implementation."""
    calls: dict[str, dict] = {}

    def fake_needs(self, **kwargs: Any) -> list[Need]:
        calls["needs"] = kwargs
        return [Need("system_role", "tester")]

    def fake_excludes(self, **kwargs: Any) -> list[Need]:
        calls["excludes"] = kwargs
        return [Need("system_role", "excluded")]

    def fake_query_filter(self, **kwargs: Any) -> Any:
        calls["query_filter"] = kwargs
        return dsl.Q("match_all")

    monkeypatch.setattr(InvenioGenerator, "needs", fake_needs, raising=True)
    monkeypatch.setattr(InvenioGenerator, "excludes", fake_excludes, raising=True)
    monkeypatch.setattr(InvenioGenerator, "query_filter", fake_query_filter, raising=True)

    gen = Generator()

    n = list(gen.needs(identity="id"))
    e = list(gen.excludes(identity="id"))
    q = gen.query_filter(identity="id")

    assert calls.keys() == {"needs", "excludes", "query_filter"}
    assert n, "Expected needs to return a value"
    assert isinstance(n[0], Need)
    assert e, "Expected excludes to return a value"
    assert isinstance(e[0], Need)
    assert hasattr(q, "to_dict")
    assert q.to_dict() == {"match_all": {}}


def test_conditional_generators_selection():
    """Selection of then_/else_ generators should follow _condition()."""

    class Dummy(InvenioGenerator):
        def __init__(self, label: str):
            self.label = label
            self.calls: list[tuple[str, dict]] = []

        def needs(self, **kwargs: Any) -> list[Need]:
            self.calls.append(("needs", kwargs))
            return [Need("system_role", self.label)]

    class ToggleCond(ConditionalGenerator):
        def __init__(self, flag: bool, then_, else_):
            super().__init__(then_, else_)
            self.flag: bool = flag

        def _condition(self, **_: Any) -> bool:
            return bool(self.flag)

    then_g = Dummy("then")
    else_g = Dummy("else")

    cond = ToggleCond(flag=True, then_=[then_g], else_=[else_g])
    list(cond.needs(identity="id"))
    assert then_g.calls
    assert then_g.calls[0][0] == "needs"
    assert not else_g.calls

    then_g.calls.clear()
    else_g.calls.clear()

    cond.flag = False
    list(cond.needs(identity="id"))
    assert else_g.calls
    assert else_g.calls[0][0] == "needs"
    assert not then_g.calls


def test_conditional_delegates_public_methods(monkeypatch):
    """Public API of ConditionalGenerator should delegate to base class."""
    calls: dict[str, dict] = {}

    def fake_needs(self, **kwargs: Any) -> list[Need]:
        calls["needs"] = kwargs
        return [Need("system_role", "tester")]

    def fake_excludes(self, **kwargs: Any) -> list[Need]:
        calls["excludes"] = kwargs
        return [Need("system_role", "excluded")]

    def fake_query_filter(self, **kwargs: Any) -> Any:
        calls["query_filter"] = kwargs
        return dsl.Q("match_all")

    monkeypatch.setattr(InvenioConditionalGenerator, "needs", fake_needs, raising=True)
    monkeypatch.setattr(InvenioConditionalGenerator, "excludes", fake_excludes, raising=True)
    monkeypatch.setattr(InvenioConditionalGenerator, "query_filter", fake_query_filter, raising=True)

    class AlwaysTrue(ConditionalGenerator):
        def __init__(self):
            super().__init__(then_=[InvenioGenerator()], else_=[InvenioGenerator()])

        def _condition(self, **kwargs: Any) -> bool:  # noqa: ARG002
            return True

    gen = AlwaysTrue()

    n = list(gen.needs(identity="id"))
    e = list(gen.excludes(identity="id"))
    q = gen.query_filter(identity="id")

    assert calls.keys() == {"needs", "excludes", "query_filter"}
    assert n
    assert isinstance(n[0], Need)
    assert e
    assert isinstance(e[0], Need)
    assert hasattr(q, "to_dict")
    assert isinstance(q.to_dict(), dict)
