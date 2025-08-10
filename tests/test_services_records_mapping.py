#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test services records mapping functionality."""

from __future__ import annotations

from unittest.mock import Mock, patch

from invenio_records_resources.services.records import (
    RecordService,
    RecordServiceConfig,
)

from oarepo_runtime.services.records.mapping import update_all_records_mappings


def test_update_all_records_mappings_with_record_services():
    """Test update_all_records_mappings with various service types."""
    # Mock services
    mock_record_service1 = Mock(spec=RecordService)
    mock_record_service1.config = Mock(spec=RecordServiceConfig)
    mock_record_service1.config.record_cls = Mock()
    mock_record_service1.config.draft_cls = Mock()

    mock_record_service2 = Mock(spec=RecordService)
    mock_record_service2.config = Mock(spec=RecordServiceConfig)
    mock_record_service2.config.record_cls = Mock()
    # No draft_cls attribute

    mock_non_record_service = Mock()  # Not a RecordService

    # Mock runtime
    mock_runtime = Mock()
    mock_runtime.services = {
        "service1": mock_record_service1,
        "service2": mock_record_service2,
        "service3": mock_non_record_service,
    }

    with (
        patch("oarepo_runtime.services.records.mapping.current_runtime", mock_runtime),
        patch("oarepo_runtime.services.records.mapping.update_record_system_fields_mapping") as mock_update,
    ):
        update_all_records_mappings()

        # Should be called for record_cls and draft_cls of service1
        # Should be called for record_cls of service2 (no draft_cls)
        # Should not be called for service3 (not a RecordService)
        expected_calls = [
            (mock_record_service1.config.record_cls,),
            (mock_record_service1.config.draft_cls,),
            (mock_record_service2.config.record_cls,),
        ]

        assert mock_update.call_count == 3
        actual_calls = [call[0] for call in mock_update.call_args_list]

        for expected_call in expected_calls:
            assert expected_call in actual_calls


def test_update_all_records_mappings_no_record_cls():
    """Test update_all_records_mappings when service has no record_cls."""
    mock_record_service = Mock(spec=RecordService)
    mock_record_service.config = Mock(spec=RecordServiceConfig)
    mock_record_service.config.record_cls = None  # No record_cls attribute
    mock_record_service.config.draft_cls = None  # No draft_cls attribute

    mock_runtime = Mock()
    mock_runtime.services = {"service1": mock_record_service}

    with (
        patch("oarepo_runtime.services.records.mapping.current_runtime", mock_runtime),
        patch("oarepo_runtime.services.records.mapping.update_record_system_fields_mapping") as mock_update,
    ):
        update_all_records_mappings()

        # Should not be called at all
        mock_update.assert_not_called()


def test_update_all_records_mappings_no_services():
    """Test update_all_records_mappings with no services."""
    mock_runtime = Mock()
    mock_runtime.services = {}

    with (
        patch("oarepo_runtime.services.records.mapping.current_runtime", mock_runtime),
        patch("oarepo_runtime.services.records.mapping.update_record_system_fields_mapping") as mock_update,
    ):
        update_all_records_mappings()

        # Should not be called at all
        mock_update.assert_not_called()


def test_update_all_records_mappings_mixed_services():
    """Test update_all_records_mappings with mix of valid and invalid services."""
    # Valid record service
    mock_record_service = Mock(spec=RecordService)
    mock_record_service.config = Mock(spec=RecordServiceConfig)
    mock_record_service.config.record_cls = Mock()
    mock_record_service.config.draft_cls = Mock()

    # Invalid service (not RecordService)
    mock_other_service = Mock()

    # Service with missing attributes
    mock_incomplete_service = Mock(spec=RecordService)
    mock_incomplete_service.config = Mock()
    mock_incomplete_service.config.record_cls = None  # No record_cls
    mock_incomplete_service.config.draft_cls = None  # No draft_cls

    mock_runtime = Mock()
    mock_runtime.services = {
        "record_service": mock_record_service,
        "other_service": mock_other_service,
        "incomplete_service": mock_incomplete_service,
    }

    with (
        patch("oarepo_runtime.services.records.mapping.current_runtime", mock_runtime),
        patch("oarepo_runtime.services.records.mapping.update_record_system_fields_mapping") as mock_update,
    ):
        update_all_records_mappings()

        # Should only be called for the valid record service
        assert mock_update.call_count == 2
        mock_update.assert_any_call(mock_record_service.config.record_cls)
        mock_update.assert_any_call(mock_record_service.config.draft_cls)


def test_update_all_records_mappings_service_config_variations():
    """Test update_all_records_mappings with various service config variations."""
    # Service with only record_cls
    mock_service_record_only = Mock(spec=RecordService)
    mock_service_record_only.config = Mock(spec=RecordServiceConfig)
    mock_service_record_only.config.record_cls = Mock()
    delattr(mock_service_record_only.config, "draft_cls")  # Remove draft_cls

    # Service with only draft_cls
    mock_service_draft_only = Mock(spec=RecordService)
    mock_service_draft_only.config = Mock(spec=RecordServiceConfig)
    mock_service_draft_only.config.draft_cls = Mock()
    delattr(mock_service_draft_only.config, "record_cls")  # Remove record_cls

    # Service with both
    mock_service_both = Mock(spec=RecordService)
    mock_service_both.config = Mock(spec=RecordServiceConfig)
    mock_service_both.config.record_cls = Mock()
    mock_service_both.config.draft_cls = Mock()

    mock_runtime = Mock()
    mock_runtime.services = {
        "record_only": mock_service_record_only,
        "draft_only": mock_service_draft_only,
        "both": mock_service_both,
    }

    with (
        patch("oarepo_runtime.services.records.mapping.current_runtime", mock_runtime),
        patch("oarepo_runtime.services.records.mapping.update_record_system_fields_mapping") as mock_update,
    ):
        update_all_records_mappings()

        # Should be called for:
        # - record_cls from record_only service
        # - draft_cls from draft_only service
        # - both record_cls and draft_cls from both service
        assert mock_update.call_count == 4

        calls = [call[0][0] for call in mock_update.call_args_list]
        assert mock_service_record_only.config.record_cls in calls
        assert mock_service_draft_only.config.draft_cls in calls
        assert mock_service_both.config.record_cls in calls
        assert mock_service_both.config.draft_cls in calls
