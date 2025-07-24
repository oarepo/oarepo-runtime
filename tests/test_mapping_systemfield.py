#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test mapping system field mixin."""

from __future__ import annotations

from invenio_records.api import Record
from invenio_records.systemfields import SystemField

from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin


class MockMappingField(MappingSystemFieldMixin, SystemField):
    """Mock mapping field for testing."""

    @property
    def mapping(self) -> dict:
        """Return test mapping."""
        return {"mapping": True}

    @property
    def mapping_settings(self) -> dict:
        """Return test mapping settings."""
        return {"settings": True}

    @property
    def dynamic_templates(self) -> list:
        """Return test dynamic templates."""
        return [{"template": True}]

    def __get__(self, record, owner=None):
        """Return the field itself for testing."""
        return self


class MockRecord(Record):
    """Mock record class for testing."""

    test_field = MockMappingField("test_field")


def test_mapping_system_field_mixin_default_mapping():
    """Test default mapping returns empty dict."""
    rec = MockRecord({})
    assert rec.test_field.mapping == {"mapping": True}


def test_mapping_system_field_mixin_default_settings():
    """Test default mapping settings returns empty dict."""
    rec = MockRecord({})
    assert rec.test_field.mapping_settings == {"settings": True}


def test_mapping_system_field_mixin_default_templates():
    """Test default dynamic templates returns empty list."""
    rec = MockRecord({})
    assert rec.test_field.dynamic_templates == [{"template": True}]
