# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test cases for the Model class resource property in oarepo_runtime.api."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

from oarepo_runtime.resources.serializers.rdm import DefaultRDMUISchema, RecordUISerializer


class MockService:
    """Mock service for testing."""

    def __init__(self):
        """Initialize the mock service."""
        self.config = MagicMock()

    @property
    def id(self):
        """Get test service id."""
        return "test"


def test_rdm_record_ui_serializer():
    """Test exports property with default value."""
    serializer = RecordUISerializer()
    schema = DefaultRDMUISchema()

    with (Path(__file__).parent / "data/datacite_export.json").open() as f:
        datacite_dict = json.load(f)

    assert serializer.dump_obj(datacite_dict) == ""
    assert schema.dump(datacite_dict=datacite_dict) == ""
