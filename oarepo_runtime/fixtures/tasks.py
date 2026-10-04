# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Celery task loading a fixture entry, so that it can be offloaded to a worker."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from celery import shared_task
from invenio_access.permissions import system_identity

from oarepo_runtime.fixtures.loader import RecordLoader


@shared_task(ignore_result=True)
def load_fixture_entry(model_code: str, app_data_folder: str, entry: dict[str, Any]) -> None:
    """Create or update a single record of the model from a fixture entry.

    Only picklable arguments are accepted so that the task can be offloaded to a worker.
    """
    RecordLoader(model_code, system_identity, Path(app_data_folder)).load(entry)
