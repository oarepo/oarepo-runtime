import warnings

from oarepo_runtime.services.custom_fields.mappings import Mapping, prepare_cf_indices

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.custom_fields.mappings.Mapping",
    DeprecationWarning,
)

__all__ = ("Mapping", "prepare_cf_indices")
