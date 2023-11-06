import warnings

from oarepo_runtime.services.config.service import PermissionsPresetsConfigMixin

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.config.service.PermissionsPresetsConfigMixin",
    DeprecationWarning,
)

__all__ = ("PermissionsPresetsConfigMixin",)
