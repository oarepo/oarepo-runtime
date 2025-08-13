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
