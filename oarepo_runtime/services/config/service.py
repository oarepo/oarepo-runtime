import inspect
from functools import cached_property

from flask import current_app


class PermissionsPresetsConfigMixin:
    components = tuple()

    @cached_property
    def permission_policy_cls(self):
        presets = self._get_preset_classes()

        permissions = {}
        for preset_class in presets:
            for permission_name, permission_needs in self._get_permissions_from_preset(
                preset_class
            ):
                target = permissions.setdefault(permission_name, [])
                for need in permission_needs:
                    if need not in target:
                        target.append(need)

        return type(f"{type(self).__name__}Permissions", tuple(presets), permissions)

    @staticmethod
    def _get_permissions_from_preset(preset_class):
        for permission_name, permission_needs in inspect.getmembers(preset_class):
            if not permission_name.startswith("can_"):
                continue
            if not isinstance(permission_needs, (list, tuple)):
                continue
            yield permission_name, permission_needs

    def _get_preset_classes(self):
        registered_preset_classes = current_app.config["OAREPO_PERMISSIONS_PRESETS"]
        preset_classes = [
            registered_preset_classes[x]
            for x in self.PERMISSIONS_PRESETS  # noqa (omitted here because of the order of mixins)
        ]
        if hasattr(self, "base_permission_policy_cls"):
            preset_classes.insert(0, self.base_permission_policy_cls)
        return preset_classes
