import warnings

from oarepo_runtime.services.facets.max_facet import MaxFacet

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.facets.max_facet.MaxFacet",
    DeprecationWarning,
)

__all__ = ("MaxFacet",)
