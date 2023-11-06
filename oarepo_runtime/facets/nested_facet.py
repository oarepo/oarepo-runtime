import warnings

from oarepo_runtime.services.facets.nested_facet import NestedLabeledFacet

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.facets.nested_facet.NestedLabeledFacet",
    DeprecationWarning,
)

__all__ = ("NestedLabeledFacet",)
