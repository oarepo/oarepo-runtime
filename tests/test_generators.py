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

from typing import Any, override

from flask_principal import Need
from invenio_records_permissions.generators import (
    ConditionalGenerator as InvenioConditionalGenerator,
)
from invenio_records_permissions.generators import (
    Disable,
)
from invenio_records_permissions.generators import Generator as InvenioGenerator
from invenio_search.engine import dsl

from oarepo_runtime.services.generators import (
    AggregateGenerator,
    ConditionalGenerator,
    Generator,
)


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

        @override
        def _condition(self, **_: Any) -> bool:
            return bool(self.flag)

        @override
        def _query_instate(self, **context: Any) -> dsl.query.Query:
            return dsl.Q()

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

    monkeypatch.setattr(InvenioConditionalGenerator, "needs", fake_needs, raising=True)
    monkeypatch.setattr(InvenioConditionalGenerator, "excludes", fake_excludes, raising=True)

    class AlwaysTrue(ConditionalGenerator):
        def __init__(self):
            super().__init__(then_=[InvenioGenerator()], else_=[InvenioGenerator()])

        @override
        def _condition(self, **kwargs: Any) -> bool:
            return True

        @override
        def _query_instate(self, **context: Any) -> dsl.query.Query:
            return dsl.Q()

    gen = AlwaysTrue()

    n = list(gen.needs(identity="id"))
    e = list(gen.excludes(identity="id"))

    assert calls.keys() == {"needs", "excludes"}
    assert n
    assert isinstance(n[0], Need)
    assert e
    assert isinstance(e[0], Need)


def test_conditional_generator_query_filter():
    """Test ConditionalGenerator query_filter method logic branches."""

    class QueryFilterGenerator(InvenioGenerator):
        def __init__(self, query=None) -> None:
            self._query = query

        @override
        def query_filter(self, **kwargs: Any) -> dsl.query.Query:
            return self._query

    class TestConditionalGenerator(ConditionalGenerator):
        def __init__(self, then_generators, else_generators, instate_query) -> None:
            super().__init__(then_=then_generators, else_=else_generators)
            self._instate_query = instate_query

        @override
        def _condition(self, **kwargs: Any) -> bool:
            # Not used in query_filter, but required for abstract method
            return True

        @override
        def _query_instate(self, **context: Any) -> dsl.query.Query:
            return self._instate_query

    # Test case 1: Both then_query and else_query exist
    is_active_query = dsl.Q("term", status="active")

    cond_gen = TestConditionalGenerator(
        then_generators=[QueryFilterGenerator(dsl.Q("term", field="then_value"))],
        else_generators=[QueryFilterGenerator(dsl.Q("term", field="else_value"))],
        instate_query=is_active_query,
    )
    result = cond_gen.query_filter()

    # Should return: (q_instate & then_query) | (~q_instate & else_query)
    expected = {
        "bool": {
            "should": [
                {
                    "bool": {
                        "must": [
                            {"term": {"status": "active"}},
                            {"term": {"field": "then_value"}},
                        ]
                    }
                },
                {
                    "bool": {
                        "must_not": [{"term": {"status": "active"}}],
                        "must": [{"term": {"field": "else_value"}}],
                    }
                },
            ]
        }
    }
    assert result.to_dict() == expected

    # Test case 2: Only then_query exists (else_query is None/empty)
    cond_gen = TestConditionalGenerator(
        then_generators=[QueryFilterGenerator(dsl.Q("term", field="then_value"))],
        else_generators=[],
        instate_query=is_active_query,
    )
    result = cond_gen.query_filter()

    # Should return: q_instate & then_query
    expected = {"bool": {"must": [{"term": {"status": "active"}}, {"term": {"field": "then_value"}}]}}
    assert result.to_dict() == expected

    # Test case 3: Only else_query exists (then_query is None/empty)
    cond_gen = TestConditionalGenerator(
        then_generators=[],
        else_generators=[QueryFilterGenerator(dsl.Q("term", field="else_value"))],
        instate_query=is_active_query,
    )
    result = cond_gen.query_filter()

    # Should return: ~q_instate & else_query
    expected = {
        "bool": {
            "must_not": [{"term": {"status": "active"}}],
            "must": [{"term": {"field": "else_value"}}],
        }
    }
    assert result.to_dict() == expected

    # Test case 4: Neither then_query nor else_query exist
    cond_gen = TestConditionalGenerator(then_generators=[], else_generators=[], instate_query=is_active_query)
    result = cond_gen.query_filter()

    # Should return: match_none query
    expected = dsl.Q("match_none")
    assert result.to_dict() == expected.to_dict()

    # Test case 5: Empty generators lists
    cond_gen = TestConditionalGenerator([QueryFilterGenerator(None)], [QueryFilterGenerator(None)], is_active_query)
    result = cond_gen.query_filter()

    # Should return: match_none query (no generators means no queries)
    expected = dsl.Q("match_none")
    assert result.to_dict() == expected.to_dict()

    # Test case 6: Multiple generators in then_ and else_
    then_gen1 = QueryFilterGenerator(dsl.Q("term", field="then1"))
    then_gen2 = QueryFilterGenerator(dsl.Q("term", field="then2"))
    else_gen1 = QueryFilterGenerator(dsl.Q("term", field="else1"))
    else_gen2 = QueryFilterGenerator(dsl.Q("match_all"))

    cond_gen = TestConditionalGenerator([then_gen1, then_gen2], [else_gen1, else_gen2], is_active_query)
    result = cond_gen.query_filter()

    expected = {
        "bool": {
            "should": [
                {
                    "bool": {
                        "should": [
                            {"term": {"field": "then1"}},
                            {"term": {"field": "then2"}},
                        ],
                        "must": [{"term": {"status": "active"}}],
                        "minimum_should_match": 1,
                    }
                },
                {
                    "bool": {
                        "must_not": [{"term": {"status": "active"}}],
                        "must": [{"match_all": {}}],
                    }
                },
            ]
        }
    }

    assert result.to_dict() == expected

    # edge cases
    cond_gen = TestConditionalGenerator(
        then_generators=[Disable()],
        else_generators=[],
        instate_query=is_active_query,
    )

    assert cond_gen.query_filter() == dsl.Q("match_none")


def test_aggregate_generator():
    """Test AggregateGenerator aggregates needs, excludes, and query_filter from multiple generators."""

    class MockGenerator(InvenioGenerator):
        def __init__(self, needs_list, excludes_list, query) -> None:
            self._needs = needs_list
            self._excludes = excludes_list
            self._query = query

        @override
        def needs(self, **kwargs: Any) -> list[Need]:
            return self._needs

        @override
        def excludes(self, **kwargs: Any) -> list[Need]:
            return self._excludes

        @override
        def query_filter(self, **kwargs: Any) -> dsl.query.Query:
            return self._query

    class TestAggregateGenerator(AggregateGenerator):
        def __init__(self, generators):
            self._gen_list = generators

        @override
        def _generators(self, **context: Any) -> list[InvenioGenerator]:
            return self._gen_list

    # Create mock generators with different needs/excludes/queries
    gen1 = MockGenerator(
        [Need("system_role", "admin")],
        [Need("system_role", "banned")],
        dsl.Q("term", field="value1"),
    )
    gen2 = MockGenerator(
        [Need("system_role", "editor"), Need("system_role", "reviewer")],
        [Need("system_role", "guest")],
        dsl.Q("term", field="value2"),
    )

    aggregate = TestAggregateGenerator([gen1, gen2])

    # Test needs aggregation
    needs = list(aggregate.needs())
    assert set(needs) == {
        Need("system_role", "admin"),
        Need("system_role", "editor"),
        Need("system_role", "reviewer"),
    }

    # Test excludes aggregation
    excludes = list(aggregate.excludes())
    assert set(excludes) == {
        Need("system_role", "banned"),
        Need("system_role", "guest"),
    }

    # Test query_filter uses _make_query to combine queries
    query = aggregate.query_filter()
    assert query == dsl.Q("term", field="value1") | dsl.Q("term", field="value2")
