# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Celery task loading a batch of fixture entries, so that it can be offloaded to a worker."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from celery import shared_task
from invenio_access.permissions import system_identity

from oarepo_runtime.fixtures.loader import RecordLoader


@shared_task(ignore_result=True)
def load_fixture_entry_batch(model_code: str, app_data_folder: str, entries: list[dict[str, Any]]) -> None:
    """Create or update a record of the model from each of the fixture entries.

    Only picklable arguments are accepted so that the task can be offloaded to a worker.
    A failing entry is logged and the remaining entries of the batch are loaded.
    """
    loader = RecordLoader(model_code, system_identity, Path(app_data_folder))
    for entry in entries:
        loader.load(entry)
