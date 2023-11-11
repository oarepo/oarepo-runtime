import warnings

from oarepo_runtime.services.facets.date import (
    AutoDateHistogramFacet,
    DateFacet,
    DateIntervalFacet,
    DateTimeFacet,
    EDTFFacet,
    EDTFIntervalFacet,
    TimeFacet,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.facets.date",
    DeprecationWarning,
)

__all__ = (
    "DateFacet",
    "TimeFacet",
    "DateTimeFacet",
    "EDTFFacet",
    "AutoDateHistogramFacet",
    "EDTFIntervalFacet",
    "DateIntervalFacet",
)
