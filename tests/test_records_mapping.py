#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test records mapping functionality."""

from __future__ import annotations

from typing import Any
from unittest.mock import Mock, patch

from invenio_records.api import Record
from invenio_search.engine import dsl

from oarepo_runtime.records.mapping import (
    get_mapping_fields,
    prefixed_index,
    update_record_index,
    update_record_system_fields_mapping,
)
from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin


class MockMappingField(MappingSystemFieldMixin):
    """Mock mapping field for testing."""

    def __init__(
        self,
        mapping: dict | None = None,
        settings: dict | None = None,
        templates: list | None = None,
    ):
        """Initialize mock field."""
        self._mapping = mapping or {}
        self._settings = settings or {}
        self._templates = templates or []

    @property
    def mapping(self) -> dict:
        """Return mapping."""
        return self._mapping

    @property
    def mapping_settings(self) -> dict:
        """Return settings."""
        return self._settings

    @property
    def dynamic_templates(self) -> list:
        """Return templates."""
        return self._templates


class MockRecord(Record):
    """Mock record with mapping fields."""

    field1 = MockMappingField(
        mapping={"title": {"type": "text"}},
        settings={"number_of_shards": 1},
        templates=[{"match": "*", "mapping": {"type": "keyword"}}],
    )
    field2 = MockMappingField(mapping={"description": {"type": "text"}})
    non_mapping_field = "not a mapping field"

    def __init__(self, data: dict | None = None, **kwargs: Any):
        """Initialize mock record."""
        super().__init__(data or {}, **kwargs)


class MockRecordNoIndex(Record):
    """Mock record without index."""

    field1 = MockMappingField(mapping={"title": {"type": "text"}})


def test_get_mapping_fields():
    """Test getting mapping fields from a record class."""
    fields = list(get_mapping_fields(MockRecord))

    assert len(fields) == 2
    assert all(isinstance(field, MappingSystemFieldMixin) for field in fields)

    # Check that the correct fields are returned
    field_mappings = [field.mapping for field in fields]
    assert {"title": {"type": "text"}} in field_mappings
    assert {"description": {"type": "text"}} in field_mappings


def test_get_mapping_fields_no_mapping_fields():
    """Test getting mapping fields from class with no mapping fields."""
    fields = list(get_mapping_fields(MockRecordNoIndex))

    assert len(fields) == 1


def test_prefixed_index(app):
    """Test prefixed_index function."""
    mock_index = Mock()
    # Set the _name attribute directly on the mock
    mock_index._name = "test-index"  # noqa: SLF001

    with patch("oarepo_runtime.records.mapping.build_alias_name") as mock_build_alias:
        mock_build_alias.return_value = "prefixed-test-index"

        result = prefixed_index(mock_index)

        assert isinstance(result, dsl.Index)
        mock_build_alias.assert_called_once_with("test-index")


@patch("oarepo_runtime.records.mapping.update_record_index")
@patch("oarepo_runtime.records.mapping.prefixed_index")
@patch("oarepo_runtime.records.mapping.get_mapping_fields")
def test_update_record_system_fields_mapping(
    mock_get_fields, mock_prefixed, mock_update_index
):
    """Test updating record system fields mapping."""
    # Setup mocks
    mock_index = Mock()
    MockRecord.index = mock_index

    mock_field1 = Mock()
    mock_field1.mapping = {"title": {"type": "text"}}
    mock_field1.mapping_settings = {"number_of_shards": 1}
    mock_field1.dynamic_templates = [{"match": "*", "mapping": {"type": "keyword"}}]

    mock_field2 = Mock()
    mock_field2.mapping = {"description": {"type": "text"}}
    mock_field2.mapping_settings = {}
    mock_field2.dynamic_templates = []

    mock_get_fields.return_value = [mock_field1, mock_field2]

    mock_prefixed_index = Mock()
    mock_prefixed.return_value = mock_prefixed_index

    # Call function
    update_record_system_fields_mapping(MockRecord)

    # Verify calls
    mock_get_fields.assert_called_once_with(MockRecord)
    mock_prefixed.assert_called_with(mock_index)

    # Should be called twice, once for each field
    assert mock_update_index.call_count == 2

    # Check first call
    first_call = mock_update_index.call_args_list[0]
    assert first_call[0][0] is mock_prefixed_index
    assert first_call[0][1] == {"number_of_shards": 1}
    assert first_call[0][2] == {"title": {"type": "text"}}
    assert first_call[0][3] == [{"match": "*", "mapping": {"type": "keyword"}}]

    # Check second call
    second_call = mock_update_index.call_args_list[1]
    assert second_call[0][0] is mock_prefixed_index
    assert second_call[0][1] == {}
    assert second_call[0][2] == {"description": {"type": "text"}}
    assert second_call[0][3] == []


def test_update_record_system_fields_mapping_no_index():
    """Test updating mapping when record has no index."""
    with patch("oarepo_runtime.records.mapping.get_mapping_fields") as mock_get_fields:
        # Should return early without calling get_mapping_fields
        update_record_system_fields_mapping(MockRecordNoIndex)
        mock_get_fields.assert_not_called()


def test_update_record_index_with_settings():
    """Test updating record index with settings."""
    mock_index = Mock()

    settings = {"number_of_shards": 2}
    mapping = {"title": {"type": "text"}}
    templates = [{"match": "*", "mapping": {"type": "keyword"}}]

    update_record_index(mock_index, settings, mapping, templates)

    # Verify index operations
    mock_index.close.assert_called_once()
    mock_index.put_settings.assert_called_once_with(body=settings)
    mock_index.open.assert_called_once()

    # Verify mapping update
    expected_body = {
        "properties": mapping,
        "dynamic_templates": templates,
    }
    mock_index.put_mapping.assert_called_once_with(body=expected_body)


def test_update_record_index_no_settings():
    """Test updating record index without settings."""
    mock_index = Mock()

    settings = {}
    mapping = {"title": {"type": "text"}}
    templates = []

    update_record_index(mock_index, settings, mapping, templates)

    # Verify index operations were not called for settings
    mock_index.close.assert_not_called()
    mock_index.put_settings.assert_not_called()
    mock_index.open.assert_not_called()

    # Verify mapping update
    expected_body = {"properties": mapping}
    mock_index.put_mapping.assert_called_once_with(body=expected_body)


def test_update_record_index_no_mapping_no_templates():
    """Test updating record index with no mapping or templates."""
    mock_index = Mock()

    settings = {}
    mapping = {}
    templates = None

    update_record_index(mock_index, settings, mapping, templates)

    # No operations should be called
    mock_index.close.assert_not_called()
    mock_index.put_settings.assert_not_called()
    mock_index.open.assert_not_called()
    mock_index.put_mapping.assert_not_called()


def test_update_record_index_empty_mapping_with_templates():
    """Test updating record index with empty mapping but with templates."""
    mock_index = Mock()

    settings = {}
    mapping = {}
    templates = [{"match": "*", "mapping": {"type": "keyword"}}]

    update_record_index(mock_index, settings, mapping, templates)

    # Verify mapping update with only templates
    expected_body = {"dynamic_templates": templates}
    mock_index.put_mapping.assert_called_once_with(body=expected_body)
