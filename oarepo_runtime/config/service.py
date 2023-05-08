from flask import current_app


class PermissionsPresetsConfigMixin:
    components = tuple()

    @property
    def permission_policy_cls(self):
        assert len(self.PERMISSIONS_PRESETS) == 1
        cls_name = current_app.config["OAREPO_PERMISSIONS_PRESETS"][
            self.PERMISSIONS_PRESETS[0]
        ]
        return cls_name
