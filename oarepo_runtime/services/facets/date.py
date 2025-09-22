#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Date facets."""

from __future__ import annotations

import re
from typing import Any

from invenio_records_resources.services.records.facets.facets import LabelledFacetMixin
from invenio_search.engine import dsl

from oarepo_runtime.services.schema.ui import (
    LocalizedDate,
    LocalizedDateTime,
    LocalizedEDTF,
    LocalizedEDTFInterval,
    LocalizedTime,
)

from .base import LabelledValuesTermsFacet


class DateFacet(LabelledValuesTermsFacet):
    """Date facet."""

    def localized_value_labels(self, values: list, locale: Any) -> dict:
        """Add date values as localize label."""
        return {val: LocalizedDate(locale=locale).format_value(val) for val in values}


class TimeFacet(LabelledValuesTermsFacet):
    """Time facet."""

    def localized_value_labels(self, values: list, locale: Any) -> dict:
        """Add date values as localize label."""
        return {val: LocalizedTime(locale=locale).format_value(val) for val in values}


class DateTimeFacet(LabelledValuesTermsFacet):
    """Date and time facet."""

    def localized_value_labels(self, values: list, locale: Any) -> dict:
        """Add date values as localize label."""
        return {val: LocalizedDateTime(locale=locale).format_value(val) for val in values}


class EDTFFacet(LabelledValuesTermsFacet):
    """Extended date time format facet."""

    def localized_value_labels(self, values: list, locale: Any) -> dict:
        """Add date values as localize label."""
        return {val: LocalizedEDTF(locale=locale).format_value(convert_to_edtf(val)) for val in values}


class AutoDateHistogramFacet(dsl.DateHistogramFacet):
    """Histogram facet."""

    agg_type = "auto_date_histogram"

    def __init__(self, **kwargs: Any):
        """Initialize histogram facet."""
        # skip DateHistogramFacet constructor
        super(dsl.DateHistogramFacet, self).__init__(**kwargs)


class EDTFIntervalFacet(LabelledFacetMixin, AutoDateHistogramFacet):  # type: ignore[override, reportIncompatibleMethodOverride]
    """Extended date time interval format facet."""

    # auto_date_histogram
    def __init__(self, *args: Any, **kwargs: Any):
        """Initialize labeled extended date time interval facet."""
        super().__init__(*args, **kwargs)

    def localized_value_labels(self, values: list, locale: Any) -> dict:
        """Add date values as localize label."""
        return {val: LocalizedEDTFInterval(locale=locale).format_value(convert_to_edtf(val)) for val in values}


class DateIntervalFacet(EDTFIntervalFacet):
    """Date interval facet."""


def convert_to_edtf(val: str) -> str:
    """Convert date to EDTF format."""
    if "/" in val:
        # interval
        return "/".join(convert_to_edtf(x) for x in val.split("/"))
    return re.sub(r"T.*", "", val)  # replace T12:00:00.000Z with nothing
