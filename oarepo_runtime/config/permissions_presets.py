import warnings

from oarepo_runtime.services.config.permissions_presets import (
    AuthenticatedPermissionPolicy,
    EveryonePermissionPolicy,
    OaiHarvesterPermissionPolicy,
    ReadOnlyPermissionPolicy,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.config.permissions_presets",
    DeprecationWarning,
)

__all__ = (
    "OaiHarvesterPermissionPolicy",
    "ReadOnlyPermissionPolicy",
    "EveryonePermissionPolicy",
    "AuthenticatedPermissionPolicy",
)
