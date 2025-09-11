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

import types
from unittest.mock import MagicMock, Mock, patch

from flask import Flask
from invenio_records.api import Record
from invenio_records.systemfields.relations import MultiRelationsField
from invenio_vocabularies.records.systemfields.relations import CustomFieldsRelation

from oarepo_runtime.records.systemfields.custom_fields import (
    get_mapping_relation_fields,
    update_record_system_fields_mapping_relation_field,
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

    field3 = MultiRelationsField(
        custom_fields=CustomFieldsRelation("CUSTOM_FIELDS_1"),
    )
    non_mapping_field = "not a mapping field"


class MockRecordNoIndex(Record):
    """Mock record without index."""

    field1 = MockMappingField(mapping={"title": {"type": "text"}})


def test_get_mapping_relation_fields():
    """Test getting mapping fields from a record class."""
    fields = list(get_mapping_relation_fields(MockRecord))

    assert len(fields) == 1
    assert all(isinstance(field, CustomFieldsRelation) for _, field in fields)

    # Check that the correct fields are returned
    assert next(iter(fields))[0] == "custom_fields"


def test_get_mapping_fields_no_mapping_relation_fields():
    """Test getting mapping fields from class with no mapping fields."""
    fields = list(get_mapping_relation_fields(MockRecordNoIndex))

    assert len(fields) == 0


@patch("oarepo_runtime.records.systemfields.custom_fields.update_record_index")
@patch("oarepo_runtime.records.systemfields.custom_fields.prefixed_index")
@patch("oarepo_runtime.records.systemfields.custom_fields.get_mapping_relation_fields")
def test_update_record_system_fields_mapping_relations(mock_get_fields, mock_prefixed, mock_update_index):
    """Test updating record system fields mapping."""
    app = Flask(__name__)
    with app.app_context():
        # Setup mocks
        mock_index = Mock()
        MockRecord.index = mock_index

        mock_customfield = Mock()
        mock_customfield._field_var = "CUSTOM_FIELDS_1"  # noqa: SLF001

        mock_field1 = Mock()
        mock_field1.fld = mock_customfield

        mock_get_fields.return_value = [("cf1", mock_field1)]

        mock_prefixed_index = Mock()
        mock_prefixed.return_value = mock_prefixed_index

        fake_cf1 = types.SimpleNamespace(name="blah", mapping={"type": "keyword"})

        with patch("oarepo_runtime.records.systemfields.custom_fields.current_app") as mock_current_app:
            # Make sure config.get returns a regular list, not a coroutine
            mock_config = MagicMock()
            mock_config.get.return_value = [fake_cf1]  # Explicitly set as list
            mock_current_app.config = mock_config

            # Call the function
            update_record_system_fields_mapping_relation_field(MockRecord)

            # Verify calls
            mock_get_fields.assert_called_once_with(MockRecord)
            mock_prefixed.assert_called_with(mock_index)

            # Should be called twice, once for each field
            assert mock_update_index.call_count == 1

            # Check first call
            first_call = mock_update_index.call_args_list[0]
            assert first_call[0][0] is mock_prefixed_index
            assert first_call[0][1] == {}
            assert first_call[0][2] == {"cf1": {"type": "object", "properties": {"blah": {"type": "keyword"}}}}
            assert first_call[0][3] is None


def test_update_record_system_fields_relations_mapping_no_index():
    """Test updating mapping when record has no index."""
    with patch("oarepo_runtime.records.systemfields.custom_fields.get_mapping_relation_fields") as mock_get_fields:
        # Should return early without calling get_mapping_fields
        update_record_system_fields_mapping_relation_field(MockRecordNoIndex)
        mock_get_fields.assert_not_called()
