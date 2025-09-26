# type: ignore  # noqa
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Drafts-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.


"""Example resource."""

from __future__ import annotations

from invenio_drafts_resources.resources import RecordResourceConfig as RecordResourceConfigBase
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
