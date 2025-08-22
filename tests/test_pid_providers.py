#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test PID providers. AI generated code."""

from __future__ import annotations

from unittest.mock import Mock, patch

import pytest
from invenio_pidstore.models import PIDStatus
from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2

from oarepo_runtime.records.pid_providers import UniversalPIDMixin


class TestUniversalPIDProvider(UniversalPIDMixin, RecordIdProviderV2):
    """Test PID provider implementation."""

    pid_type = "test"


def test_universal_pid_mixin_attributes():
    """Test UniversalPIDMixin has correct attributes."""
    assert UniversalPIDMixin.unpid_pid_type == "recid"
    assert UniversalPIDMixin.unpid_default_status == PIDStatus.REGISTERED


@patch("oarepo_runtime.records.pid_providers.PersistentIdentifier.create")
def test_universal_pid_mixin_create_success(mock_pid_create, app, db):
    """Test successful PID creation."""
    # Mock the parent create method
    mock_provider = Mock()
    mock_provider.pid = Mock()
    mock_provider.pid.pid_value = "test-123"

    with patch.object(RecordIdProviderV2, "create", return_value=mock_provider):
        result = TestUniversalPIDProvider.create(
            object_type="rec",
            object_uuid="uuid-123",
            options={"test": "value"},
        )

        # Assert parent create was called
        RecordIdProviderV2.create.assert_called_once_with(
            object_type="rec",
            object_uuid="uuid-123",
            options={"test": "value"},
        )

        # Assert universal PID was created
        mock_pid_create.assert_called_once_with(
            "recid",
            "test-123",
            pid_provider=None,
            object_type="rec",
            object_uuid="uuid-123",
            status=PIDStatus.REGISTERED,
        )

        assert result is mock_provider


@patch("oarepo_runtime.records.pid_providers.PersistentIdentifier.create")
def test_universal_pid_mixin_create_no_pid_value(mock_pid_create, app, db):
    """Test PID creation when pid_value is None."""
    # Mock the parent create method with None pid_value
    mock_provider = Mock()
    mock_provider.pid = Mock()
    mock_provider.pid.pid_value = None

    with patch.object(RecordIdProviderV2, "create", return_value=mock_provider):
        with pytest.raises(ValueError, match="PID value cannot be None."):
            TestUniversalPIDProvider.create(
                object_type="rec",
                object_uuid="uuid-123",
            )

        # Assert universal PID was not created
        mock_pid_create.assert_not_called()


@patch("oarepo_runtime.records.pid_providers.PersistentIdentifier.create")
def test_universal_pid_mixin_create_with_minimal_params(mock_pid_create, app, db):
    """Test PID creation with minimal parameters."""
    mock_provider = Mock()
    mock_provider.pid = Mock()
    mock_provider.pid.pid_value = "minimal-123"

    with patch.object(RecordIdProviderV2, "create", return_value=mock_provider):
        result = TestUniversalPIDProvider.create()

        # Assert parent create was called with None parameters
        RecordIdProviderV2.create.assert_called_once_with(
            object_type=None,
            object_uuid=None,
            options=None,
        )

        # Assert universal PID was created with correct parameters
        mock_pid_create.assert_called_once_with(
            "recid",
            "minimal-123",
            pid_provider=None,
            object_type=None,
            object_uuid=None,
            status=PIDStatus.REGISTERED,
        )

        assert result is mock_provider


@patch("oarepo_runtime.records.pid_providers.PersistentIdentifier.create")
def test_universal_pid_mixin_create_with_kwargs(mock_pid_create, app, db):
    """Test PID creation with additional keyword arguments."""
    mock_provider = Mock()
    mock_provider.pid = Mock()
    mock_provider.pid.pid_value = "kwargs-123"

    with patch.object(RecordIdProviderV2, "create", return_value=mock_provider):
        result = TestUniversalPIDProvider.create(
            object_type="rec",
            object_uuid="uuid-123",
            custom_param="value",
            another_param=42,
        )

        # Assert parent create was called with kwargs
        RecordIdProviderV2.create.assert_called_once_with(
            object_type="rec",
            object_uuid="uuid-123",
            options=None,
            custom_param="value",
            another_param=42,
        )

        # Assert universal PID was created
        mock_pid_create.assert_called_once_with(
            "recid",
            "kwargs-123",
            pid_provider=None,
            object_type="rec",
            object_uuid="uuid-123",
            status=PIDStatus.REGISTERED,
        )

        assert result is mock_provider


def test_universal_pid_mixin_custom_attributes():
    """Test customizing UniversalPIDMixin attributes."""

    class CustomUniversalPIDProvider(UniversalPIDMixin, RecordIdProviderV2):
        unpid_pid_type = "custom_unpid"
        unpid_default_status = PIDStatus.NEW

    assert CustomUniversalPIDProvider.unpid_pid_type == "custom_unpid"
    assert CustomUniversalPIDProvider.unpid_default_status == PIDStatus.NEW
