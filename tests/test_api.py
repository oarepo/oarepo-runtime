#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test cases for the Model class resource property in oarepo_runtime.api."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from oarepo_runtime.api import Model
from oarepo_runtime.proxies import current_runtime


class MockService:
    """Mock service for testing."""

    def __init__(self):
        """Initialize the mock service."""
        self.config = MagicMock()


def test_resource_with_string_import():
    """Test resource property with valid string import path."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,
        resource="invenio_records_resources.resources.records.resource.RecordResource",
        resource_config=MagicMock(),
    )

    # Mock the resource class and its instantiation
    with patch("oarepo_runtime.api.obj_or_import_string") as mock_import:
        mock_resource_class = MagicMock()
        mock_import.return_value = mock_resource_class

        resource = (  # noqa: F841 # Access the resource property to trigger import
            model.resource
        )

        mock_import.assert_called_once_with("invenio_records_resources.resources.records.resource.RecordResource")
        mock_resource_class.assert_called_once_with(service=service, config=model.resource_config)


def test_resource_with_none_import():
    """Test resource property raises ValueError when obj_or_import_string returns None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,
        resource="nonexistent.resource.Class",
        resource_config=MagicMock(),
    )

    # Mock obj_or_import_string to return None
    with patch("oarepo_runtime.api.obj_or_import_string") as mock_import:
        mock_import.return_value = None

        with pytest.raises(
            ValueError,
            match=r"Resource class nonexistent\.resource\.Class can not be None\.",
        ):
            _ = model.resource


def test_resource_with_direct_instance():
    """Test resource property with direct resource instance."""
    service = MockService()
    resource_instance = MagicMock()

    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,
        resource=resource_instance,
        resource_config=MagicMock(),
    )

    assert model.resource is resource_instance


def test_api_blueprint_name():
    """Test api_blueprint_name property."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,
        resource_config=MagicMock(blueprint_name="test_blueprint"),
    )

    assert model.api_blueprint_name == "test_blueprint"


def test_api_url(app):
    """Test api_url method."""
    model = current_runtime.models["vocabularies"]
    search_url = model.api_url("search", type="languages")
    assert search_url.endswith("/api/vocabularies/languages")


def test_code_property():
    """Test code property."""
    service = MockService()
    model = Model(
        code="test_model_code",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.code == "test_model_code"


def test_name_property():
    """Test name property."""
    service = MockService()
    model = Model(
        code="test",
        name="Test Model Name",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.name == "Test Model Name"


def test_version_property():
    """Test version property."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="2.1.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.version == "2.1.0"


def test_description_property():
    """Test description property with value."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        description="This is a test model description",
    )

    assert model.description == "This is a test model description"


def test_description_property_none():
    """Test description property when None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.description is None


def test_records_alias_enabled_property_default():
    """Test records_alias_enabled property with default value."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.records_alias_enabled is True


def test_records_alias_enabled_property_false():
    """Test records_alias_enabled property when set to False."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        records_alias_enabled=False,
    )

    assert model.records_alias_enabled is False


def test_ui_model_property_default():
    """Test ui_model property with default value."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.ui_model == {}


def test_ui_model_property_with_value():
    """Test ui_model property with custom value."""
    service = MockService()
    ui_model_data = {"key1": "value1", "key2": {"nested": "value"}}
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        ui_model=ui_model_data,
    )

    assert model.ui_model == ui_model_data


def test_file_service_property():
    """Test file_service property."""
    service = MockService()
    file_service_mock = MagicMock()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        file_service=file_service_mock,
    )

    assert model.file_service is file_service_mock


def test_file_service_property_none():
    """Test file_service property when None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.file_service is None


def test_draft_file_service_property():
    """Test draft_file_service property."""
    service = MockService()
    draft_file_service_mock = MagicMock()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        draft_file_service=draft_file_service_mock,
    )

    assert model.draft_file_service is draft_file_service_mock


def test_draft_file_service_property_none():
    """Test draft_file_service property when None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.draft_file_service is None


def test_media_file_service_property():
    """Test media_file_service property."""
    service = MockService()
    media_file_service_mock = MagicMock()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        media_file_service=media_file_service_mock,
    )

    assert model.media_file_service is media_file_service_mock


def test_media_file_service_property_none():
    """Test media_file_service property when None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.media_file_service is None


def test_media_draft_file_service_property():
    """Test media_draft_file_service property."""
    service = MockService()
    media_draft_file_service_mock = MagicMock()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        media_draft_file_service=media_draft_file_service_mock,
    )

    assert model.media_draft_file_service is media_draft_file_service_mock


def test_media_draft_file_service_property_none():
    """Test media_draft_file_service property when None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.media_draft_file_service is None


def test_exports_property_default():
    """Test exports property with default value."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.exports == []


def test_exports_property_with_value():
    """Test exports property with custom value."""
    from oarepo_runtime.api import Export

    service = MockService()
    export_mock = MagicMock(spec=Export)
    exports_list = [export_mock]

    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        exports=exports_list,
    )

    assert model.exports == exports_list


def test_model_metadata_property_none():
    """Test model_metadata property when None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.model_metadata is None


def test_model_metadata_property_with_value():
    """Test model_metadata property with custom value."""
    from oarepo_runtime.api import ModelMetadata

    service = MockService()
    model_metadata_mock = MagicMock(spec=ModelMetadata)
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        model_metadata=model_metadata_mock,
    )

    assert model.model_metadata == model_metadata_mock


def test_features_property_none():
    """Test model_metadata property when None."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.features is None


def test_features_property_with_value():
    """Test model_metadata property with custom value."""
    service = MockService()
    features_mock = MagicMock({"files": {"version": "1.0.0"}})
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        features=features_mock,
    )

    assert model.features == features_mock


def test_imports_property_default():
    """Test imports property with default value."""
    service = MockService()
    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
    )

    assert model.imports == []


def test_imports_property_with_value():
    """Test imports property with custom value."""
    from oarepo_runtime.api import Import

    service = MockService()
    import_mock = MagicMock(spec=Import)
    imports_list = [import_mock]

    model = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service,  # type: ignore[arg-type]
        resource_config=MagicMock(),
        imports=imports_list,
    )

    assert model.imports == imports_list
