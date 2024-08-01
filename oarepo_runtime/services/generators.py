import warnings

from .permissions import RecordOwners

warnings.warn(
    "oarepo_runtime.services.generators is deprecated, import RecordOwners from "
    "oarepo_runtime.services.permissions",
    DeprecationWarning,
)
__all__ = ("RecordOwners",)
