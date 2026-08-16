#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test cases for the InternalRelations system field and its lookup table."""

from __future__ import annotations

import pytest
from invenio_records import Record
from marshmallow import ValidationError

from oarepo_runtime.records.systemfields.relations import (
    InternalRelations,
    InternalRelationsLookup,
)


class TestRecord(Record):
    """Test record with internal relations."""

    internal_relations = InternalRelations(target_paths=["proteins", "instruments", "nested.reagents"])


def test_internal_relations_class_access():
    """Accessing the field on the class (not an instance) returns the field itself."""
    assert isinstance(TestRecord.internal_relations, InternalRelations)
    assert TestRecord.internal_relations.target_paths == ["proteins", "instruments", "nested.reagents"]


def test_internal_relations_lookup_instance():
    """Accessing the field on a record instance returns a lookup bound to that record."""
    rec = TestRecord({"proteins": [], "instruments": []})
    lookup = rec.internal_relations
    assert isinstance(lookup, InternalRelationsLookup)
    assert lookup.record is rec
    assert lookup.target_paths == ["proteins", "instruments", "nested.reagents"]


def test_lookup_table_simple_list():
    rec = TestRecord(
        {
            "proteins": [
                {"id": "p1", "name": "Protein 1"},
                {"id": "p2", "name": "Protein 2"},
            ],
            "instruments": [{"id": "i1", "name": "Instrument 1"}],
        }
    )
    assert rec.internal_relations.lookup_table == {
        "proteins": {
            "p1": {"id": "p1", "name": "Protein 1"},
            "p2": {"id": "p2", "name": "Protein 2"},
        },
        "instruments": {
            "i1": {"id": "i1", "name": "Instrument 1"},
        },
        "nested.reagents": {},
    }


def test_lookup_table_scalar_value():
    """A path that holds a single dict (not a list) is collected as well."""
    rec = TestRecord({"proteins": {"id": "p1", "name": "Protein 1"}, "instruments": []})
    table = rec.internal_relations.lookup_table
    assert table["proteins"] == {"p1": {"id": "p1", "name": "Protein 1"}}


def test_lookup_table_nested_lists_are_flattened():
    """Arbitrarily nested lists along the path are flattened into a single mapping."""
    rec = TestRecord(
        {
            "proteins": [
                [{"id": "p1", "name": "Protein 1"}],
                [{"id": "p2", "name": "Protein 2"}, {"id": "p3", "name": "Protein 3"}],
            ],
            "instruments": [],
        }
    )
    table = rec.internal_relations.lookup_table
    assert table["proteins"] == {
        "p1": {"id": "p1", "name": "Protein 1"},
        "p2": {"id": "p2", "name": "Protein 2"},
        "p3": {"id": "p3", "name": "Protein 3"},
    }


def test_lookup_table_missing_path():
    """A target path absent from the record data collects to an empty mapping."""
    rec = TestRecord({"instruments": [{"id": "i1"}]})
    table = rec.internal_relations.lookup_table
    assert table["proteins"] == {}
    assert table["instruments"] == {"i1": {"id": "i1"}}
    assert table["nested.reagents"] == {}


def test_lookup_table_dotted_path_through_dict():
    """A dotted path segment ("nested") that holds a dict is traversed transparently."""
    rec = TestRecord(
        {
            "instruments": [],
            "nested": {"reagents": {"id": "r1", "name": "Reagent 1"}},
        }
    )
    table = rec.internal_relations.lookup_table
    assert table["nested.reagents"] == {"r1": {"id": "r1", "name": "Reagent 1"}}


def test_lookup_table_dotted_path_through_list():
    """A dotted path segment ("nested") that holds a list is flattened before continuing."""
    rec = TestRecord(
        {
            "instruments": [],
            "nested": [
                {"reagents": {"id": "r1", "name": "Reagent 1"}},
                {"reagents": {"id": "r2", "name": "Reagent 2"}},
            ],
        }
    )
    table = rec.internal_relations.lookup_table
    assert table["nested.reagents"] == {
        "r1": {"id": "r1", "name": "Reagent 1"},
        "r2": {"id": "r2", "name": "Reagent 2"},
    }


def test_lookup_table_duplicate_id_raises():
    rec = TestRecord(
        {
            "proteins": [{"id": "dup", "name": "A"}, {"id": "dup", "name": "B"}],
            "instruments": [],
        }
    )
    with pytest.raises(ValidationError, match="Duplicate id 'dup'"):
        _ = rec.internal_relations


def test_lookup_table_reflects_current_record_state():
    """The lookup table is rebuilt on every access - it is not cached on the record."""
    rec = TestRecord({"proteins": [{"id": "p1"}], "instruments": []})
    assert rec.internal_relations.lookup_table["proteins"] == {"p1": {"id": "p1"}}

    rec["proteins"].append({"id": "p2"})
    assert rec.internal_relations.lookup_table["proteins"] == {
        "p1": {"id": "p1"},
        "p2": {"id": "p2"},
    }


@pytest.fixture
def rec_for_contains_getitem():
    return TestRecord(
        {
            "proteins": [{"id": "p1", "name": "Protein 1"}],
            "instruments": [{"id": "i1", "name": "Instrument 1"}],
        }
    )


def test_contains_true_for_known_path_and_id(rec_for_contains_getitem):
    assert ("proteins", "p1") in rec_for_contains_getitem.internal_relations
    assert ("instruments", "i1") in rec_for_contains_getitem.internal_relations


def test_contains_false_for_unknown_id(rec_for_contains_getitem):
    assert ("proteins", "unknown") not in rec_for_contains_getitem.internal_relations


def test_contains_false_for_unknown_path(rec_for_contains_getitem):
    """A path that was never configured in target_paths does not raise, just returns False."""
    assert ("unknown_path", "p1") not in rec_for_contains_getitem.internal_relations


def test_getitem_returns_the_enclosing_dict(rec_for_contains_getitem):
    assert rec_for_contains_getitem.internal_relations[("proteins", "p1")] == {
        "id": "p1",
        "name": "Protein 1",
    }


def test_getitem_raises_keyerror_for_unknown_id(rec_for_contains_getitem):
    with pytest.raises(KeyError):
        _ = rec_for_contains_getitem.internal_relations[("proteins", "unknown")]


def test_getitem_raises_keyerror_for_unknown_path(rec_for_contains_getitem):
    with pytest.raises(KeyError):
        _ = rec_for_contains_getitem.internal_relations[("unknown_path", "p1")]
