#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Records dumpers."""

from __future__ import annotations

from typing import Any, ClassVar

from invenio_records.dumpers import SearchDumper as InvenioSearchDumper
from invenio_records.dumpers import SearchDumperExt


class SearchDumper(InvenioSearchDumper):
    """A custom dumper class that extends the InvenioSearchDumper."""

    extensions: ClassVar[list[SearchDumperExt]] = []

    def __init__(self, **kwargs: Any) -> None:
        """Initialize the SearchDumper with custom extensions."""
        super().__init__(extensions=self.extensions, **kwargs)
