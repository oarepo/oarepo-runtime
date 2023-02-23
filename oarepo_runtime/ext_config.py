from oarepo_runtime.config.permissions_presets import (
    EveryonePermissionPolicy,
    ReadOnlyPermissionPolicy,
)

OAREPO_PERMISSIONS_PRESETS = {
    "read_only": ReadOnlyPermissionPolicy,
    "everyone": EveryonePermissionPolicy,
}
