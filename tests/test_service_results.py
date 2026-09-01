# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Test service results."""

from __future__ import annotations

from unittest.mock import Mock, PropertyMock, patch

import pytest
from invenio_access.permissions import Identity
from invenio_records.api import Record
from invenio_records_resources.services.records.results import (
    RecordList as BaseRecordList,
)

from oarepo_runtime.services.results import RecordItem, RecordList, ResultComponent
from oarepo_runtime.typing import record_from_result


class MockResultComponent(ResultComponent):
    """Mock result component for testing."""

    def update_data(self, identity: Identity, record: Record, projection: dict, expand: bool) -> None:
        """Update projection with test data."""
        _ = record  # Unused but required by interface
        projection["result_component"] = True
        projection["component_identity"] = str(identity.id)
        projection["expand"] = expand


class MockRecordItem(RecordItem):
    """Mock record item with components."""

    components = (MockResultComponent,)


class MockRecordList(RecordList):
    """Mock record list with components."""

    components = (MockResultComponent,)


def test_result_component_abstract_method():
    """Test that ResultComponent.update_data is abstract."""
    component = ResultComponent()

    with pytest.raises(NotImplementedError):
        component.update_data(Identity(1), Record({}), {}, expand=False)


def test_result_component_initialization():
    """Test ResultComponent initialization."""
    mock_item = Mock()
    mock_list = Mock()

    component = ResultComponent(record_item=mock_item, record_list=mock_list)

    assert component._record_item is mock_item  # noqa: SLF001
    assert component._record_list is mock_list  # noqa: SLF001


def test_record_item_data_with_components():
    """Test RecordItem data property with components."""
    mock_record = Mock(spec=Record)
    mock_identity = Identity(1)
    mock_schema = Mock()

    # Setup the base data
    base_data = {"title": "Test Record", "id": "123"}
    mock_schema.dump.return_value = base_data

    item = MockRecordItem(
        service=Mock(),
        identity=mock_identity,
        record=mock_record,
        schema=mock_schema,
        expand=False,  # Don't expand to avoid field resolution
    )

    # Set the _data to None to ensure it's not cached
    item._data = None  # noqa: SLF001

    result = item.data

    # Should have the component data added
    assert result["title"] == "Test Record"
    assert result["id"] == "123"
    assert result["result_component"] is True
    assert result["component_identity"] == "1"
    assert result["expand"] is False


def test_record_item_data_caching():
    """Test that RecordItem data is cached."""
    mock_record = Mock(spec=Record)
    mock_identity = Identity(1)
    mock_schema = Mock()

    base_data = {"title": "Test Record"}
    mock_schema.dump.return_value = base_data

    item = MockRecordItem(
        service=Mock(),
        identity=mock_identity,
        record=mock_record,
        schema=mock_schema,
    )

    # First access should process components and cache
    result1 = item.data

    # Set the _data to simulate caching
    item._data = result1  # noqa: SLF001

    # Second access should return cached data
    result2 = item.data

    # Should be the same object (cached)
    assert result1 is result2


def test_record_item_errors_postprocessing():
    """Test RecordItem error postprocessing."""
    item = RecordItem(
        service=Mock(),
        identity=Identity(1),
        record=Mock(),
        schema=Mock(),
        errors=[
            {"field": "title", "messages": ["Required field."]},
            {"field": "description", "messages": "Invalid value"},
        ],
    )

    errors = item.errors

    assert len(errors) == 2
    assert {"field": "title", "messages": ["Required field."]} in errors
    assert {"field": "description", "messages": "Invalid value"} in errors


def test_record_item_to_dict_with_errors():
    """Test RecordItem to_dict method with errors."""
    mock_schema = Mock()
    base_data = {"title": "Test"}
    mock_schema.dump.return_value = base_data

    item = RecordItem(
        service=Mock(),
        identity=Identity(1),
        record=Mock(),
        schema=mock_schema,
        errors=[{"field": "title", "messages": ["Error"]}],
    )

    with patch.object(RecordItem, "data", new_callable=PropertyMock) as mock_data:
        mock_data.return_value = base_data

        result = item.to_dict()

        assert result["title"] == "Test"
        assert "errors" in result
        assert len(result["errors"]) == 1


def test_record_item_to_dict_no_errors():
    """Test RecordItem to_dict method without errors."""
    mock_schema = Mock()
    base_data = {"title": "Test"}
    mock_schema.dump.return_value = base_data

    item = RecordItem(
        service=Mock(),
        identity=Identity(1),
        record=Mock(),
        schema=mock_schema,
    )

    assert record_from_result(item) is item._record  # noqa: SLF001

    with patch.object(RecordItem, "data", new_callable=PropertyMock) as mock_data:
        mock_data.return_value = base_data

        result = item.to_dict()

        assert result["title"] == "Test"
        assert "errors" not in result


def test_record_item_postprocess_error_messages_string_list():
    """Test postprocessing error messages with string list."""
    item = RecordItem(Mock(), Identity(1), Mock(), Mock())

    messages = ["Error 1", "Error 2"]
    result = list(item.postprocess_error_messages("field1", messages))

    assert len(result) == 1
    assert result[0] == {"field": "field1", "messages": ["Error 1", "Error 2"]}


def test_record_item_postprocess_error_messages_mixed():
    """Test postprocessing error messages with mixed types."""
    item = RecordItem(Mock(), Identity(1), Mock(), Mock())

    messages = ["String error", {"nested": "error"}]

    result = list(item.postprocess_error_messages("field1", messages))

    # When there are both string and non-string messages, only the string messages are processed
    # The non-string messages are ignored because the implementation has an if/else structure
    assert len(result) == 1
    assert result[0] == {"field": "field1", "messages": ["String error"]}


def test_record_item_postprocess_error_messages_non_string():
    """Test postprocessing error messages with non-string."""
    item = RecordItem(Mock(), Identity(1), Mock(), Mock())

    messages = {"field": "error"}

    result = list(item.postprocess_error_messages("field1", messages))

    assert len(result) == 1
    assert result[0] == {"field": "field1", "messages": {"field": "error"}}


def test_record_list_aggregations_processing():
    """Test RecordList aggregations processing."""
    mock_results = []
    mock_service = Mock()

    record_list = RecordList(
        service=mock_service,
        identity=Identity(1),
        results=mock_results,
        params={},
        links_tpl=Mock(),
        links_item_tpl=Mock(),
        schema=Mock(),
    )

    # Mock the parent aggregations property
    mock_aggregations = {
        "status": {
            "buckets": [
                {"key": 123, "label": 456, "doc_count": 5},
                {"key": "published", "label": "Published", "doc_count": 10},
            ]
        }
    }

    with patch.object(BaseRecordList, "aggregations", new_callable=PropertyMock) as mock_agg:
        mock_agg.return_value = mock_aggregations

        result = record_list.aggregations

        # Check that numeric keys and labels were converted to strings
        buckets = result["status"]["buckets"]
        assert buckets[0]["key"] == "123"
        assert buckets[0]["label"] == "456"
        assert buckets[1]["key"] == "published"
        assert buckets[1]["label"] == "Published"

        # Check that non-string keys and labels are converted to strings
        buckets = result["status"]["buckets"]
        assert buckets[0]["key"] == "123"
        assert buckets[0]["label"] == "456"
        assert buckets[1]["key"] == "published"
        assert buckets[1]["label"] == "Published"


def test_record_list_aggregations_none():
    """Test RecordList aggregations when None."""
    mock_results = []
    mock_service = Mock()

    record_list = RecordList(
        service=mock_service,
        identity=Identity(1),
        results=mock_results,
        params={},
        links_tpl=Mock(),
        links_item_tpl=Mock(),
        schema=Mock(),
    )

    with patch.object(RecordList, "aggregations", new_callable=PropertyMock) as mock_agg:
        mock_agg.return_value = None

        result = record_list.aggregations

        assert result is None


def test_record_list_aggregations_attribute_error():
    """Test RecordList aggregations with AttributeError."""
    mock_results = []
    mock_service = Mock()

    record_list = RecordList(
        service=mock_service,
        identity=Identity(1),
        results=mock_results,
        params={},
        links_tpl=Mock(),
        links_item_tpl=Mock(),
        schema=Mock(),
    )

    with patch.object(BaseRecordList, "aggregations", new_callable=PropertyMock) as mock_agg:
        mock_agg.side_effect = AttributeError()

        result = record_list.aggregations

        assert result is None


def test_record_item_postprocess_error_messages_only_non_string():
    """Test postprocessing when only non-string messages exist.

    This covers lines 102-103 where _iter_errors_dict is called.
    """
    item = RecordItem(Mock(), Identity(1), Mock(), Mock())

    # Only non-string messages (dict), no strings
    messages = [{"nested": "error"}, {"another": "field"}]

    result = list(item.postprocess_error_messages("field1", messages))

    # Should iterate over non-string messages and yield from _iter_errors_dict
    assert len(result) == 2
    # _iter_errors_dict wraps messages in a list
    assert result[0] == {"field": "field1.nested", "messages": ["error"]}
    assert result[1] == {"field": "field1.another", "messages": ["field"]}


def test_record_item_postprocess_errors_without_messages_key():
    """Test postprocess_errors when error has no 'messages' key.

    This covers line 112 where the error is appended directly.
    """
    item = RecordItem(Mock(), Identity(1), Mock(), Mock())

    errors = [
        {"field": "title", "messages": ["Required"]},
        {"field": "id", "code": "invalid"},  # No 'messages' key
    ]

    result = item.postprocess_errors(errors)

    assert len(result) == 2
    assert result[0] == {"field": "title", "messages": ["Required"]}
    assert result[1] == {"field": "id", "code": "invalid"}


def test_record_list_hits_with_links_search_item():
    """Test RecordList hits when links_search_item and links_search_item_tpl are set.

    This covers line 173 where custom links template is used.
    """
    # Use Mock without spec to allow to_dict
    mock_record = Mock()
    mock_record.to_dict.return_value = {"id": "123", "versions": {}}
    mock_results = [mock_record]
    mock_service = Mock()
    mock_schema = Mock()
    mock_schema.dump.return_value = {"id": "123"}

    # Custom links templates
    mock_links_search_item = "items/{id}"
    mock_links_item_template = Mock(expand=Mock(return_value={"self": "/items/123"}))
    mock_links_search_item_tpl = Mock(return_value=mock_links_item_template)
    mock_service.config.links_search_item = mock_links_search_item
    mock_service.config.search_item_links_template = mock_links_search_item_tpl
    mock_service.record_cls = Mock()
    mock_service.record_cls.loads = Mock(return_value=mock_record)

    # Use MockRecordList which has components defined
    record_list = MockRecordList(
        service=mock_service,
        identity=Identity(1),
        results=mock_results,
        params={},
        links_tpl=None,
        links_item_tpl=None,
        schema=mock_schema,
    )

    hits = list(record_list.hits)

    assert len(hits) == 1
    assert hits[0]["links"] == {"self": "/items/123"}
    assert hits[0].get("result_component") is True  # Component was called
    mock_links_search_item_tpl.assert_called_once_with(mock_links_search_item)


def test_record_list_hits_without_links_tpl():
    """Test RecordList hits when links_tpl is None.

    This covers line 177->181 where links are not added.
    """
    # Use Mock without spec to allow to_dict
    mock_record = Mock()
    mock_record.to_dict.return_value = {"id": "123", "versions": {}}
    mock_results = [mock_record]
    mock_service = Mock()
    mock_schema = Mock()
    mock_schema.dump.return_value = {"id": "123"}

    mock_service.config = Mock()
    mock_service.config.links_search_item = None
    mock_service.config.search_item_links_template = None
    mock_service.record_cls = Mock()
    mock_service.record_cls.loads = Mock(return_value=mock_record)

    # Use MockRecordList which has components defined
    record_list = MockRecordList(
        service=mock_service,
        identity=Identity(1),
        results=mock_results,
        params={},
        links_tpl=None,
        links_item_tpl=None,
        schema=mock_schema,
    )

    hits = list(record_list.hits)

    assert len(hits) == 1
    assert "links" not in hits[0]
    assert hits[0].get("result_component") is True  # Component was called


def test_record_list_hits_with_draft_record():
    """Test RecordList hits when processing a draft record.

    This covers lines 156-159 where draft_class.loads is used.
    """
    mock_record = Mock()
    # Trigger the draft branch with is_latest_draft=True and is_latest=False
    mock_record.to_dict.return_value = {
        "id": "123",
        "versions": {"is_latest_draft": True, "is_latest": False},
    }
    mock_results = [mock_record]
    mock_service = Mock()
    mock_schema = Mock()
    mock_schema.dump.return_value = {"id": "123"}

    mock_service.config = Mock()
    mock_service.config.links_search_item = None
    mock_service.config.search_item_links_template = None

    # Setup both record_cls and draft_cls
    mock_service.record_cls = Mock()
    mock_service.record_cls.loads = Mock(return_value=mock_record)

    mock_draft_cls = Mock()
    mock_service.draft_cls = mock_draft_cls
    mock_draft_cls.loads = Mock(return_value=mock_record)

    # Use MockRecordList which has components defined
    record_list = MockRecordList(
        service=mock_service,
        identity=Identity(1),
        results=mock_results,
        params={},
        links_tpl=None,
        links_item_tpl=None,
        schema=mock_schema,
    )

    hits = list(record_list.hits)

    assert len(hits) == 1
    # draft_cls.loads should have been called, not record_cls.loads
    mock_draft_cls.loads.assert_called_once_with(mock_record.to_dict())
    assert hits[0].get("result_component") is True


# zmena
@pytest.mark.parametrize(
    ("hit_dict", "expected_loader"),
    [
        (
            {"id": "123", "versions": {"is_latest_draft": True, "is_latest": False}},
            "draft",
        ),
        ({"id": "123", "publication_status": "draft"}, "draft"),
        ({"id": "123", "versions": {"is_latest": True}}, "record"),
    ],
)

def test_record_list_hits_selects_correct_class(hit_dict, expected_loader):
    mock_hit = Mock()
    mock_hit.to_dict.return_value = hit_dict
    mock_loaded_record = Mock()
    mock_service = Mock()
    mock_schema = Mock()
    mock_schema.dump.return_value = {"id": "123"}

    mock_service.config = Mock()
    mock_service.config.links_search_item = None
    mock_service.config.search_item_links_template = None
    mock_service.record_cls = Mock()
    mock_service.record_cls.loads = Mock(return_value=mock_loaded_record)
    mock_service.draft_cls = Mock()
    mock_service.draft_cls.loads = Mock(return_value=mock_loaded_record)

    record_list = MockRecordList(
        service=mock_service,
        identity=Identity(1),
        results=[mock_hit],
        params={},
        links_tpl=None,
        links_item_tpl=None,
        schema=mock_schema,
    )

    hits = list(record_list.hits)

    assert len(hits) == 1
    if expected_loader == "draft":
        mock_service.draft_cls.loads.assert_called_once_with(hit_dict)
        mock_service.record_cls.loads.assert_not_called()
    else:
        mock_service.record_cls.loads.assert_called_once_with(hit_dict)
        mock_service.draft_cls.loads.assert_not_called()
