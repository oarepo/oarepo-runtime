from flask import current_app


class PermissionsPresetsConfigMixin:
    components = tuple()

    @property
    def permission_policy_cls(self):
        preset_classes = current_app.config["OAREPO_PERMISSIONS_PRESETS"]
        presets = [preset_classes[x] for x in self.PERMISSIONS_PRESETS]
        if hasattr(self, "base_permission_policy_cls"):
            presets.insert(0, self.base_permission_policy_cls)
        return type(f"{type(self).__name__}Permissions", tuple(presets), {})
