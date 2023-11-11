import warnings

from oarepo_runtime.services.facets.base import LabelledValuesTermsFacet

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.facets.based.LabelledValuesTermsFacet",
    DeprecationWarning,
)

__all__ = ("LabelledValuesTermsFacet",)
