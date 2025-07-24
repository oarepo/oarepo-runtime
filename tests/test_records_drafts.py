#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test records drafts functionality."""

from __future__ import annotations

from unittest.mock import Mock, patch

from invenio_records.api import Record

from oarepo_runtime.records.drafts import get_draft, has_draft


class MockDraftRecord(Record):
    """Mock draft record."""

    is_draft = True


class MockPublishedRecord(Record):
    """Mock published record."""

    is_draft = False
    has_draft = False
    parent = Mock()


class MockPublishedRecordWithDraft(Record):
    """Mock published record with draft."""

    is_draft = False
    has_draft = True
    parent = Mock()


class MockVocabularyRecord(Record):
    """Mock vocabulary record (no parent, no has_draft)."""

    is_draft = False


def test_has_draft_with_draft_record():
    """Test has_draft with a draft record."""
    record = MockDraftRecord({})
    assert has_draft(record) is True


def test_has_draft_with_published_record_with_draft():
    """Test has_draft with published record that has draft."""
    record = MockPublishedRecordWithDraft({})

    with patch("oarepo_runtime.records.drafts.get_draft") as mock_get_draft:
        mock_get_draft.return_value = Mock()  # Return a draft

        assert has_draft(record) is True
        mock_get_draft.assert_called_once_with(record)


def test_has_draft_with_vocabulary_record():
    """Test has_draft with vocabulary record (no parent)."""
    record = MockVocabularyRecord({})
    assert has_draft(record) is False


def test_get_draft_with_draft_record():
    """Test get_draft with a draft record returns itself."""
    record = MockDraftRecord({})
    assert get_draft(record) is record


def test_get_draft_with_vocabulary_record():
    """Test get_draft with vocabulary record returns None."""
    record = MockVocabularyRecord({})
    assert get_draft(record) is None


def test_get_draft_with_published_record_no_parent():
    """Test get_draft with published record without parent."""
    record = Record({})
    record.is_draft = False
    # No parent attribute

    assert get_draft(record) is None


def test_get_draft_with_published_record_no_has_draft():
    """Test get_draft with published record without has_draft."""
    record = Record({})
    record.is_draft = False
    record.parent = Mock()
    # No has_draft attribute

    assert get_draft(record) is None


def test_get_draft_with_published_record_has_draft(app):
    """Test get_draft with published record that has a draft."""
    record = MockPublishedRecordWithDraft({})

    # Mock the runtime and service
    mock_service = Mock()
    mock_service.config = Mock()
    mock_draft_cls = Mock()
    mock_service.config.draft_cls = mock_draft_cls

    mock_draft = Mock()
    mock_draft_cls.get_records_by_parent.return_value = iter([mock_draft])

    with patch("oarepo_runtime.records.drafts.current_runtime") as mock_runtime:
        mock_runtime.get_record_service_for_record = Mock(return_value=mock_service)
        result = get_draft(record)

        assert result is mock_draft
        mock_runtime.get_record_service_for_record.assert_called_once_with(record)
        mock_draft_cls.get_records_by_parent.assert_called_once_with(record.parent, with_deleted=False)


@patch("oarepo_runtime.records.drafts.current_runtime")
def test_get_draft_with_published_record_no_draft_found(app):
    """Test get_draft when no draft is found."""
    record = MockPublishedRecordWithDraft({})

    # Mock the runtime and service
    mock_service = Mock()
    mock_service.config = Mock()
    mock_draft_cls = Mock()
    mock_service.config.draft_cls = mock_draft_cls

    # Return empty iterator (no drafts found)
    mock_draft_cls.get_records_by_parent.return_value = iter([])

    with patch("oarepo_runtime.records.drafts.current_runtime") as mock_runtime:
        mock_runtime.get_record_service_for_record = Mock(return_value=mock_service)
        result = get_draft(record)

        assert result is None
        mock_runtime.get_record_service_for_record.assert_called_once_with(record)
        mock_draft_cls.get_records_by_parent.assert_called_once_with(record.parent, with_deleted=False)


@patch("oarepo_runtime.records.drafts.current_runtime")
def test_get_draft_multiple_drafts_returns_first(mock_runtime, app):
    """Test get_draft when multiple drafts exist, returns the first one."""
    record = MockPublishedRecordWithDraft({})

    # Mock the runtime and service
    mock_service = Mock()
    mock_service.config = Mock()
    mock_draft_cls = Mock()
    mock_service.config.draft_cls = mock_draft_cls

    mock_draft1 = Mock()
    mock_draft2 = Mock()
    mock_draft_cls.get_records_by_parent.return_value = iter([mock_draft1, mock_draft2])

    with patch("oarepo_runtime.records.drafts.current_runtime") as mock_runtime:
        mock_runtime.get_record_service_for_record = Mock(return_value=mock_service)
        result = get_draft(record)

        # Should return the first draft
        assert result is mock_draft1
        mock_runtime.get_record_service_for_record.assert_called_once_with(record)
        mock_draft_cls.get_records_by_parent.assert_called_once_with(record.parent, with_deleted=False)
