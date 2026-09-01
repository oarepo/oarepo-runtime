# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Base facet with label."""

from __future__ import annotations

from typing import Any

from invenio_records_resources.services.records.facets import TermsFacet


class LabelledValuesTermsFacet(TermsFacet):
    """Define labelled facet."""

    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize labeled facet."""
        super().__init__(*args, **{"value_labels": self.value_labels, **kwargs})

    def localized_value_labels(self, values: list, locale: str) -> dict:
        """Add date values as localize label."""
        _ = locale
        return {val: val for val in values}

    def value_labels(self, values: list) -> dict:
        """Add date values as label."""
        return {val: val for val in values}
