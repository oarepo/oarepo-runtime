import warnings

from oarepo_runtime.services.custom_fields.mappings import Mapping

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.custom_fields.mappings.Mapping",
    DeprecationWarning,
)

__all__ = ("Mapping",)

