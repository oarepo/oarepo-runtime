# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Test cases for the InternalRelation relation field and its result class.

Mirrors the coverage in test_arbitrary_relations.py (validate, dereference, resolve
via call, set_value), but for a relation that resolves to a part of the same record
(via the InternalRelations lookup table) instead of an external PID-resolved record.
"""

from __future__ import annotations

import pytest
from invenio_records import Record
from invenio_records.systemfields import MultiRelationsField
from invenio_records.systemfields.relations.errors import InvalidRelationValue

from oarepo_runtime.records.systemfields.relations import InternalRelation, InternalRelations


class TestRecord(Record):
    """Test record with an internal_relations lookup table and internal relation fields."""

    internal_relations = InternalRelations()

    relations = MultiRelationsField(
        primary_protein=InternalRelation(
            array_paths=[],
            relation_field="primary_protein",
            target_path="proteins",
            keys=["name"],
        ),
        used_instruments=InternalRelation(
            array_paths=["used_instruments"],
            target_path="instruments",
            keys=["name"],
        ),
    )


@pytest.fixture
def ok_data():
    return {
        "proteins": [
            {"id": "p1", "name": "Protein One"},
            {"id": "p2", "name": "Protein Two"},
        ],
        "instruments": [
            {"id": "i1", "name": "Instrument One"},
        ],
        "primary_protein": {"id": "p1"},
        "used_instruments": [{"id": "i1"}],
    }


@pytest.fixture
def bad_data():
    return {
        "proteins": [{"id": "p1", "name": "Protein One"}],
        "instruments": [{"id": "i1", "name": "Instrument One"}],
        "primary_protein": {"id": "unknown"},
        "used_instruments": [{"id": "unknown"}],
    }


def test_resolve_scalar_with_call(ok_data):
    rec = TestRecord(ok_data)
    assert rec.relations.primary_protein() == {"id": "p1", "name": "Protein One"}


def test_resolve_list_with_call(ok_data):
    rec = TestRecord(ok_data)
    assert list(rec.relations.used_instruments()) == [{"id": "i1", "name": "Instrument One"}]


def test_resolve_scalar_unknown_id_returns_none(bad_data):
    rec = TestRecord(bad_data)
    assert rec.relations.primary_protein() is None


def test_resolve_list_unknown_id_returns_none_item(bad_data):
    rec = TestRecord(bad_data)
    assert list(rec.relations.used_instruments()) == [None]


def test_validate_ok(ok_data):
    rec = TestRecord(ok_data)
    rec.relations.validate()


def test_validate_failure(bad_data):
    rec = TestRecord(bad_data)
    with pytest.raises(InvalidRelationValue):
        rec.relations.validate()


def test_dereference(ok_data):
    rec = TestRecord(ok_data)
    rec.relations.dereference()
    assert rec["primary_protein"]["name"] == "Protein One"
    assert rec["used_instruments"][0]["name"] == "Instrument One"


def test_set_value_not_implemented(ok_data):
    """set_value is a deliberate NotImplementedError stub for now."""
    rec = TestRecord(ok_data)
    with pytest.raises(NotImplementedError):
        rec.relations.primary_protein = "p2"
