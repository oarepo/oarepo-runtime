import inspect
from functools import cached_property

from flask import current_app


class PermissionsPresetsConfigMixin:
    components = tuple()

    @cached_property
    def permission_policy_cls(self):
        preset_classes = current_app.config["OAREPO_PERMISSIONS_PRESETS"]
        presets = [preset_classes[x] for x in self.PERMISSIONS_PRESETS]
        if hasattr(self, "base_permission_policy_cls"):
            presets.insert(0, self.base_permission_policy_cls)

        permissions = {}
        for preset_class in presets:
            for permission_name, permission_needs in inspect.getmembers(preset_class):
                if not permission_name.startswith("can_"):
                    continue
                if not isinstance(permission_needs, (list, tuple)):
                    continue
                target = permissions.setdefault(permission_name, [])
                for need in permission_needs:
                    if need not in target:
                        target.append(need)
        return type(f"{type(self).__name__}Permissions", tuple(presets), permissions)
