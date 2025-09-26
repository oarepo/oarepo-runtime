#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for GroupedFacetsParam."""

from __future__ import annotations

import types
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any
from unittest.mock import Mock

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_access.permissions import system_user_id
from invenio_records_resources.services.records.facets import TermsFacet
from invenio_search.engine import dsl

from oarepo_runtime.services.facets.nested_facet import NestedLabeledFacet
from oarepo_runtime.services.facets.params import GroupedFacetsParam
from oarepo_runtime.services.facets.utils import build_facet, get_basic_facet

if TYPE_CHECKING:
    from flask import Flask
    from invenio_records_resources.services.records import RecordService

# Helper function used via current_app.config["OAREPO_FACET_GROUP_NAME"]


def find_groups(_identity: Identity, _config: Any, _extra: Any) -> list[str]:
    return ["from_config_func"]


def _dummy_config(
    facets: dict[str, Any],
    facet_groups: dict[str, dict[str, Any]] | None = None,
) -> types.SimpleNamespace:
    obj = types.SimpleNamespace()
    obj.facets = facets
    if facet_groups is not None:
        obj.facet_groups = facet_groups
    return obj


def test_identity_facet_groups_via_config_function(
    app: Flask, identity_simple: Identity, service: RecordService
) -> None:
    app.config["OAREPO_FACET_GROUP_NAME"] = find_groups
    try:
        params = GroupedFacetsParam(service.config.search)
        groups = params.identity_facet_groups(identity_simple)
        assert groups == ["from_config_func"]
    finally:
        app.config.pop("OAREPO_FACET_GROUP_NAME", None)


def test_identity_facet_groups_from_role_needs() -> None:
    ident = Identity(123)
    ident.provides.add(UserNeed(123))
    ident.provides.add(Need(method="role", value="curator"))
    cfg = _dummy_config({})
    params = GroupedFacetsParam(cfg)  # type: ignore[arg-type]
    assert params.identity_facet_groups(ident) == ["curator"]


def test_facet_groups_property_present_and_absent() -> None:
    facet_obj = {"publication_status": TermsFacet(field="publication_status")}
    groups = {
        "default": ["publication_status"],
        "admin": ["publication_status"],
    }
    params_with = GroupedFacetsParam(_dummy_config(facet_obj, groups))
    result = params_with.facet_groups

    # type: ignore[arg-type]
    assert set(result.keys()) == {"admin", "default"}
    assert set(result["admin"].keys()) == {"publication_status"}
    assert set(result["default"].keys()) == {"publication_status"}

    assert result["admin"]["publication_status"] is facet_obj["publication_status"]
    assert result["default"]["publication_status"] is facet_obj["publication_status"]

    params_without = GroupedFacetsParam(_dummy_config(facet_obj))  # type: ignore[arg-type]
    assert params_without.facet_groups is None


def test_facet_builder() -> None:
    facets = get_basic_facet(
        {},
        None,
        "metadata.jej.c.keyword",
        [],
        "invenio_records_resources.services.records.facets.TermsFacet",
    )

    assert "metadata.jej.c" in facets
    assert facets["metadata.jej.c"] == [
        {
            "facet": "invenio_records_resources.services.records.facets.TermsFacet",
            "field": "metadata.jej.c.keyword",
            "label": "metadata/jej/c.label",
        }
    ]
    facets = get_basic_facet(
        {},
        {
            "facet": "oarepo_runtime.services.facets.date.EDTFIntervalFacet",
            "field": "vlastni.cesta",
            "label": "jeeej",
        },
        "metadata.jej.c.keyword",
        [],
        "invenio_records_resources.services.records.facets.TermsFacet",
    )
    assert "metadata.jej.c" in facets
    assert facets["metadata.jej.c"] == [
        {
            "facet": "oarepo_runtime.services.facets.date.EDTFIntervalFacet",
            "field": "vlastni.cesta",
            "label": "jeeej",
        }
    ]


def test_labelled_facet():
    facet = build_facet(
        [
            {
                "facet": "oarepo_runtime.services.facets.base.LabelledValuesTermsFacet",
                "path": "metadata.additionalTitles.title",
                "label": "kchchch",
            },
        ]
    )
    value_labels = facet.value_labels(["1970-01-01"])
    assert value_labels == {"1970-01-01": "1970-01-01"}

    value_labels = facet.localized_value_labels(["1970-01-01"], "en")
    assert value_labels == {"1970-01-01": "1970-01-01"}


def test_build_facet():
    facet = build_facet(
        [
            {
                "facet": "invenio_records_resources.services.records.facets.TermsFacet",
                "label": "jej/c.label",
                "field": "jej.c",
            }
        ]
    )

    assert facet._params == {"field": "jej.c"}  # noqa: SLF001
    assert str(facet._label) == "jej/c.label"  # noqa: SLF001
    facet = build_facet(
        [
            {
                "facet": "oarepo_runtime.services.facets.nested_facet.NestedLabeledFacet",
                "path": "metadata.additionalTitles.title",
            },
            {
                "facet": "invenio_records_resources.services.records.facets.TermsFacet",
                "field": "metadata.additionalTitles.title.lang",
                "label": "kchchch",
            },
        ]
    )
    assert isinstance(facet, NestedLabeledFacet)
    facet_filter = facet.add_filter([])
    assert facet_filter is None
    facet_filter = facet.add_filter(["jej"])
    assert facet_filter.to_dict() == {
        "path": "metadata.additionalTitles.title",
        "query": {"terms": {"metadata.additionalTitles.title.lang": ["jej"]}},
        "type": "nested",
    }
    labelled_values = facet.get_labelled_values({}, [])
    assert "kchchch" in labelled_values.values()

    assert facet._path == "metadata.additionalTitles.title"  # noqa: SLF001
    assert isinstance(facet._inner, TermsFacet)  # noqa: SLF001
    assert facet._inner._params == {"field": "metadata.additionalTitles.title.lang"}  # noqa: SLF001
    with pytest.raises(ValueError, match=r"Facet class can not be None\."):
        build_facet(
            [
                {
                    "facet": None,
                    "label": "jej/c.label",
                    "field": "jej.c",
                }
            ]
        )

    with pytest.raises(ValueError, match=r"Facet class can not be None\."):
        build_facet(
            [
                {
                    "facet": None,
                    "path": "metadata.additionalTitles.title",
                },
                {
                    "facet": "invenio_records_resources.services.records.facets.TermsFacet",
                    "label": "jej/c.label",
                    "field": "jej.c",
                },
            ]
        )


def test_nested_labeled_facet():
    inner = Mock()
    inner.get_values.return_value = {"kchchch": "value"}

    facet = NestedLabeledFacet(path="metadata.additionalTitles.title", nested_facet=inner, label="kchchch")
    data = SimpleNamespace(inner={"some": "payload"})
    filter_values = ["x", "y"]

    result = facet.get_values(data, filter_values)
    inner.get_values.assert_called_once_with({"some": "payload"}, filter_values)
    assert result == {"kchchch": "value"}


def test_identity_facets_without_groups_returns_all(service: RecordService, identity_simple: Identity) -> None:
    params = GroupedFacetsParam(service.config.search)
    assert params.identity_facets(identity_simple) == params.facets


def test_identity_facets_system_user_or_process_returns_all() -> None:
    f = {"publication_status": TermsFacet(field="publication_status")}
    groups = {"default": {"publication_status": TermsFacet(field="publication_status")}}

    # System user ID
    ident_sys = Identity(system_user_id)
    ident_sys.provides.add(UserNeed(system_user_id))
    params_sys = GroupedFacetsParam(_dummy_config(f, groups))  # type: ignore[arg-type]
    assert params_sys.identity_facets(ident_sys) == params_sys.facets

    # System process need
    ident_proc = Identity(42)
    ident_proc.provides.add(UserNeed(42))
    ident_proc.provides.add(Need(method="system_process", value="any"))
    params_proc = GroupedFacetsParam(_dummy_config(f, groups))  # type: ignore[arg-type]
    assert params_proc.identity_facets(ident_proc) == params_proc.facets


def test_filter_user_facets_with_groups_and_side_effect_mutation() -> None:
    all_facets = {
        "publication_status": TermsFacet(field="publication_status"),
        "another": TermsFacet(field="another"),
    }
    facet_groups = {
        "default": {"publication_status": TermsFacet(field="publication_status")},
        "curator": {"another": TermsFacet(field="another")},
    }
    ident = Identity(2)
    ident.provides.add(UserNeed(2))
    ident.provides.add(Need(method="role", value="curator"))

    params = GroupedFacetsParam(_dummy_config(all_facets, facet_groups))  # type: ignore[arg-type]

    # Before: facets contain both
    assert set(params.facets.keys()) == {"publication_status", "another"}

    user_facets = params.identity_facets(ident)

    # After: user facets should be default + curator
    assert set(user_facets.keys()) == {"publication_status", "another"}

    # Side effect: params.facets was cleared in _filter_user_facets
    assert params.facets == {}


def test_aggregate_with_user_facets_adds_aggs() -> None:
    search = dsl.Search()
    user_facets = {"publication_status": TermsFacet(field="publication_status")}
    params = GroupedFacetsParam(_dummy_config(user_facets))  # type: ignore[arg-type]

    search = params.aggregate_with_user_facets(search, user_facets)
    aggs = search.to_dict().get("aggs", {})
    assert set(aggs.keys()) == {"publication_status"}


def test_filter_builds_and_applies_filters() -> None:
    facets = {"publication_status": TermsFacet(field="publication_status")}
    params = GroupedFacetsParam(_dummy_config(facets))  # type: ignore[arg-type]
    params.add_filter("publication_status", ["published"])  # populate internal _filters

    search = dsl.Search()
    search = params.filter(search)
    sdict = search.to_dict()

    # Both query.filter and post_filter should be present
    assert "post_filter" in sdict
    assert "query" in sdict
    assert "bool" in sdict["query"]
    assert "filter" in sdict["query"]["bool"]


def test_apply_adds_aggs_filters_and_selected_values(identity_simple: Identity) -> None:
    facets = {"publication_status": TermsFacet(field="publication_status")}
    params_obj: dict[str, Any] = {"facets": {"publication_status": ["published"]}}

    params = GroupedFacetsParam(_dummy_config(facets))  # type: ignore[arg-type]

    search = dsl.Search()
    search = params.apply(identity_simple, search, params_obj)

    # Aggregations present
    aggs = search.to_dict().get("aggs", {})
    assert set(aggs.keys()) == {"publication_status"}

    # Filters present (both filter and post_filter)
    sdict = search.to_dict()
    assert "post_filter" in sdict
    assert "query" in sdict
    assert "bool" in sdict["query"]
    assert "filter" in sdict["query"]["bool"]

    # Selected values added back to params_obj
    assert params_obj.get("publication_status") == ["published"]


def test_apply_respects_grouped_facets(identity_simple: Identity) -> None:
    all_facets = {
        "publication_status": TermsFacet(field="publication_status"),
        "another": TermsFacet(field="another"),
    }
    facet_groups = {"default": {"publication_status": TermsFacet(field="publication_status")}}

    params = GroupedFacetsParam(_dummy_config(all_facets, facet_groups))  # type: ignore[arg-type]

    params_dict: dict[str, Any] = {"facets": {"publication_status": ["published"], "another": ["x"]}}

    search = dsl.Search()
    search = params.apply(identity_simple, search, params_dict)

    # Only default facet should be aggregated for non-system identities
    aggs = search.to_dict().get("aggs", {})
    assert set(aggs.keys()) == {"publication_status"}

    # Selected values should still be reflected back
    assert params_dict.get("publication_status") == ["published"]
