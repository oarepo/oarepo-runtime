# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Tests for the bulk-indexing cap patched into RecordIndexer."""

from __future__ import annotations

from unittest.mock import Mock

from invenio_indexer.api import RecordIndexer

from oarepo_runtime import indexers


def test_process_bulk_queue_is_patched_with_default_max_items(app, monkeypatch):
    """The app finalization patches RecordIndexer, which caps a bulk task at 1000 items by default."""
    assert RecordIndexer.process_bulk_queue is indexers._process_bulk_queue

    orig = Mock(return_value=0)
    monkeypatch.setattr(indexers, "_orig_process_bulk_queue", orig)
    indexer = RecordIndexer()

    indexer.process_bulk_queue()

    orig.assert_called_once_with(indexer, search_bulk_kwargs=None, bulk_index_max_items=1000)
