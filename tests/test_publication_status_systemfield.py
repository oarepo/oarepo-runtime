#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test record status system field."""

from __future__ import annotations

import pytest
from invenio_drafts_resources.records.api import Draft
from invenio_records_resources.records.api import Record

from oarepo_runtime.records.systemfields.publication_status import (
    PublicationStatusSystemField,
)


class MockRecord(Record):  # type: ignore[misc]
    """Mock record class for testing."""

    publication_status = PublicationStatusSystemField()


class MockDraftRecord(Draft):  # type: ignore[misc]
    """Mock draft record class for testing."""

    publication_status = PublicationStatusSystemField()


def test_publication_status_field_mapping():
    """Test that the status field has correct mapping."""
    field = PublicationStatusSystemField()
    mapping = field.mapping

    assert field.key in mapping
    assert mapping[field.key]["type"] == "keyword"


def test_publication_status_field_published_record():
    """Test status field returns 'published' for non-draft records."""
    record = MockRecord({"title": "Test"})

    # Access status field directly
    assert record.publication_status == "published"


def test_publication_status_field_draft_record():
    """Test status field returns 'draft' for draft records."""
    record = MockDraftRecord({"title": "Test Draft"})

    # Access status field directly
    assert record.publication_status == "draft"


def test_publication_status_field_class_access():
    """Test accessing the field from the class returns the field itself."""
    field = MockRecord.publication_status
    assert isinstance(field, PublicationStatusSystemField)


def test_publication_status_field_post_load():
    """Test that post_load removes status from data."""
    field = PublicationStatusSystemField()
    record = MockRecord({})
    data = {"status": "draft", "title": "Test"}

    field.post_load(record, data)

    # Status should be removed from data (using field's attr_name)
    assert field.attr_name not in data
    assert "title" in data


def test_publication_status_field_post_load_no_status():
    """Test post_load when status is not in data."""
    field = PublicationStatusSystemField()
    record = MockRecord({})
    data = {"title": "Test"}

    # Should not raise an error
    field.post_load(record, data)
    assert data == {"title": "Test"}


def test_publication_status_field_post_dump():
    """Test that post_dump adds status to data."""
    record = MockRecord({})
    data = {"title": "Test"}

    MockRecord.publication_status.post_dump(record, data)

    # Status should be added to data using attr_name
    assert data[MockRecord.publication_status.attr_name] == "published"
    assert data["title"] == "Test"


def test_publication_status_field_post_dump_draft():
    """Test post_dump with draft record."""
    record = MockDraftRecord({})
    data = {"title": "Test"}

    MockDraftRecord.publication_status.post_dump(record, data)

    # Status should be added to data using attr_name
    assert data[MockDraftRecord.publication_status.attr_name] == "draft"
    assert data["title"] == "Test"


def test_publication_status_field_post_dump_no_key():
    """Test post_dump when field has no key."""
    # Create a field without a key
    record = MockRecord({})
    data = {"title": "Test"}

    MockRecord.publication_status.post_dump(record, data)
    assert data == {"title": "Test", "publication_status": "published"}


def test_publication_status_field_invalid_attr_name():
    """Test field with invalid attribute name."""
    field = PublicationStatusSystemField()

    # Mock the attr_name to be invalid
    original_attr_name = field.attr_name
    try:
        # Use object.__setattr__ to bypass property setter
        object.__setattr__(field, "_attr_name", 123)

        with pytest.raises(TypeError):
            field.__get__(MockRecord(), MockRecord)
    finally:
        # Restore original attr_name
        object.__setattr__(field, "_attr_name", original_attr_name)
