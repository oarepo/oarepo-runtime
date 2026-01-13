#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

import pytest
from invenio_records_permissions.generators import AnyUser, Disable, SystemProcess

from oarepo_runtime.services.generators import IfDraftType
from oarepo_runtime.typing import record_from_result


def assert_matches(record, generator) -> None:
    """Check if a record matches the given generator.

    The generator returns system_process needs if matched, otherwise an empty list.
    """
    assert generator._condition(record=record)  # noqa: SLF001
    needs = generator.needs(record=record)
    assert len(needs) > 0  # SystemProcess should provide needs


def assert_not_matches(record, generator) -> None:
    """Check if a record does not match the given generator.

    The generator returns an empty list of needs if not matched.
    """
    assert not generator._condition(record=record)  # noqa: SLF001
    needs = generator.needs(record=record)
    assert len(needs) == 0  # Disable should provide no needs


def test_if_draft_generators(app, db, search_with_field_mapping, service, search_clear, identity_simple, location):
    """Test IfDraftType with initial draft (newly created, not published)."""
    # Create a draft (initial draft)

    generator_for_state_initial = IfDraftType("initial", then_=[SystemProcess()], else_=[Disable()])
    generator_for_state_metadata = IfDraftType("metadata", then_=[SystemProcess()], else_=[Disable()])
    generator_for_state_new_version = IfDraftType("new_version", then_=[SystemProcess()], else_=[Disable()])

    rec = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Initial Draft"},
            "files": {"enabled": False},
        },
    )

    assert_matches(record_from_result(rec), generator_for_state_initial)
    assert_not_matches(record_from_result(rec), generator_for_state_metadata)
    assert_not_matches(record_from_result(rec), generator_for_state_new_version)

    rec = service.publish(identity_simple, rec.id)

    # published record should not match any draft type
    assert_not_matches(record_from_result(rec), generator_for_state_initial)
    assert_not_matches(record_from_result(rec), generator_for_state_metadata)
    assert_not_matches(record_from_result(rec), generator_for_state_new_version)

    rec = service.edit(identity_simple, rec.id)

    assert_not_matches(record_from_result(rec), generator_for_state_initial)
    assert_matches(record_from_result(rec), generator_for_state_metadata)
    assert_not_matches(record_from_result(rec), generator_for_state_new_version)

    # Test that new_version still doesn't match
    rec = service.publish(identity_simple, rec.id)

    assert_not_matches(record_from_result(rec), generator_for_state_initial)
    assert_not_matches(record_from_result(rec), generator_for_state_metadata)
    assert_not_matches(record_from_result(rec), generator_for_state_new_version)

    rec = service.new_version(identity_simple, rec.id)

    assert_not_matches(record_from_result(rec), generator_for_state_initial)
    assert_not_matches(record_from_result(rec), generator_for_state_metadata)
    assert_matches(record_from_result(rec), generator_for_state_new_version)


def test_if_draft_generators_without_record(
    app, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
    """Test IfDraftType when record is None."""
    generator_for_state_initial = IfDraftType("initial", then_=[SystemProcess()], else_=[Disable()])
    generator_for_state_metadata = IfDraftType("metadata", then_=[SystemProcess()], else_=[Disable()])
    generator_for_state_new_version = IfDraftType("new_version", then_=[SystemProcess()], else_=[Disable()])
    assert_not_matches(None, generator_for_state_initial)
    assert_not_matches(None, generator_for_state_metadata)
    assert_not_matches(None, generator_for_state_new_version)


def create_query(qf):
    """Create query filter that returns query tree for qf & Any user || not qf & Disable."""
    return {
        "bool": {
            "should": [
                {
                    "bool": {
                        "should": [qf],
                        "minimum_should_match": 1,
                        "must": [{"match_all": {}}],
                    }
                },
                {
                    "bool": {
                        "must_not": [qf],
                        "must": [{"match_none": {}}],
                    }
                },
            ]
        }
    }


@pytest.mark.parametrize(
    ("draft_types", "generated_json"),
    [
        (
            "initial",
            create_query(
                {
                    "bool": {
                        "must": [
                            {"term": {"versions.index": 1}},
                            {"term": {"metadata.is_latest_draft": True}},
                        ]
                    }
                }
            ),
        ),
        (
            "metadata",
            create_query({"match_none": {}}),
        ),
        (
            "new_version",
            create_query({"match_none": {}}),
        ),
    ],
)
def test_filter_matches(
    app,
    db,
    search_with_field_mapping,
    service,
    search_clear,
    identity_simple,
    location,
    draft_types,
    generated_json,
):
    """Test query_filter for initial draft type."""
    generator = IfDraftType(draft_types, then_=[AnyUser()], else_=[Disable()])

    # Get the query filter
    query = generator.query_filter().to_dict()

    assert query == generated_json
