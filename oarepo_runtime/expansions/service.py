import warnings

from oarepo_runtime.services.expansions.service import ExpandableFieldsServiceMixin

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.expansions.service.ExpandableFieldsServiceMixin",
    DeprecationWarning,
)

__all__ = ("ExpandableFieldsServiceMixin",)
