# SPDX-FileCopyrightText: 2020 CERN
# SPDX-License-Identifier: MIT

"""Example resource."""

from __future__ import annotations

from invenio_drafts_resources.resources import (
    RecordResourceConfig as RecordResourceConfigBase,
)
from invenio_records_resources.resources import (
    FileResourceConfig as FileResourceConfigBase,
)


class RecordResourceConfig(RecordResourceConfigBase):
    """Mock record resource configuration."""

    blueprint_name = "mocks"
    url_prefix = "/mocks"


class FileResourceConfig(FileResourceConfigBase):
    """Mock record file resource."""

    blueprint_name = "mocks_files"
    url_prefix = "/mocks/<pid_value>"


class DraftFileResourceConfig(FileResourceConfigBase):
    """Mock record file resource."""

    blueprint_name = "mocks_draft_files"
    url_prefix = "/mocks/<pid_value>/draft"
