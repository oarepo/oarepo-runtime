#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Unit tests: record_dict_to_linkset/record_dict_to_json_linkset with missing DataCite export."""

from unittest.mock import MagicMock, patch

from oarepo_runtime.resources.signposting import (
    record_dict_to_json_linkset,
    record_dict_to_linkset,
)


def _mock_runtime(raise_=None, return_=None):
    """Return a runtime stub that raises or returns on get_export_from_serialized_record."""
    m = MagicMock()
    if raise_ is not None:
        m.get_export_from_serialized_record.side_effect = raise_
    else:
        m.get_export_from_serialized_record.return_value = return_
    return m


class TestRecordDictToLinksetMissingDatacite:
    """record_dict_to_linkset must not crash when DataCite export is absent."""

    def test_returns_empty_string_on_value_error(self):
        """ValueError from missing export must produce an empty string, not HTTP 500."""
        runtime = _mock_runtime(raise_=ValueError("No export found for mimetype"))
        with patch(
            "oarepo_runtime.resources.signposting.current_runtime",
            new=runtime,
        ):
            result = record_dict_to_linkset({})
        assert result == "", f"Expected '' got {result!r}"

    def test_returns_empty_string_on_key_error(self):
        runtime = _mock_runtime(raise_=KeyError("datacite"))
        with patch(
            "oarepo_runtime.resources.signposting.current_runtime",
            new=runtime,
        ):
            result = record_dict_to_linkset({})
        assert result == ""

    def test_delegates_to_create_linkset_on_success(self):
        """When export succeeds, the datacite dict must be forwarded to create_linkset."""
        datacite_stub = {"titles": [{"title": "Test"}]}
        runtime = _mock_runtime(return_=datacite_stub)
        create_linkset_mock = MagicMock(return_value="link-header-value")
        with (
            patch(
                "oarepo_runtime.resources.signposting.current_runtime",
                new=runtime,
            ),
            patch(
                "oarepo_runtime.resources.signposting.create_linkset",
                new=create_linkset_mock,
            ),
        ):
            result = record_dict_to_linkset({"links": {"self_html": "https://example.com"}})
        create_linkset_mock.assert_called_once()
        assert result == "link-header-value"


class TestRecordDictToJsonLinksetMissingDatacite:
    """record_dict_to_json_linkset must not crash when DataCite export is absent."""

    def test_returns_empty_dict_on_value_error(self):
        """ValueError from missing export must produce {}, not HTTP 500."""
        runtime = _mock_runtime(raise_=ValueError("No export found for mimetype"))
        with patch(
            "oarepo_runtime.resources.signposting.current_runtime",
            new=runtime,
        ):
            result = record_dict_to_json_linkset({})
        assert result == {}

    def test_returns_empty_dict_on_key_error(self):
        runtime = _mock_runtime(raise_=KeyError("datacite"))
        with patch(
            "oarepo_runtime.resources.signposting.current_runtime",
            new=runtime,
        ):
            result = record_dict_to_json_linkset({})
        assert result == {}

    def test_delegates_to_create_linkset_json_on_success(self):
        datacite_stub = {"titles": [{"title": "Test"}]}
        runtime = _mock_runtime(return_=datacite_stub)
        create_linkset_json_mock = MagicMock(return_value={"linkset": []})
        with (
            patch(
                "oarepo_runtime.resources.signposting.current_runtime",
                new=runtime,
            ),
            patch(
                "oarepo_runtime.resources.signposting.create_linkset_json",
                new=create_linkset_json_mock,
            ),
        ):
            result = record_dict_to_json_linkset({"links": {"self_html": "https://example.com"}})
        create_linkset_json_mock.assert_called_once()
        assert result == {"linkset": []}
