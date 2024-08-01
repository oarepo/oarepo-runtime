import inspect
import re
from typing import List, Type

from flask import current_app
from invenio_records_permissions import BasePermissionPolicy

from oarepo_runtime.utils.functools import class_property


class PermissionsPresetsConfigMixin:
    components = tuple()
    PERMISSIONS_PRESETS_CONFIG_KEY = None
    # PERMISSIONS_PRESETS = []         # noqa (omitted here because of the order of mixins)

    @class_property
    def permission_policy_cls(cls):
        """
        Returns a class that contains all permissions from the presets.

        Needs to be a class property as invenio-vocabularies, unlike other invenio records,
        do not instantiate the service configuration class, but use it as a class.
        """
        presets = cls._get_preset_classes()

        permissions = {}
        for preset_class in presets:
            for permission_name, permission_needs in cls._get_permissions_from_preset(
                preset_class
            ):
                target = permissions.setdefault(permission_name, [])
                for need in permission_needs:
                    if need not in target:
                        target.append(need)

        return type(f"{cls.__name__}Permissions", tuple(presets), permissions)

    @staticmethod
    def _get_permissions_from_preset(preset_class):
        for permission_name, permission_needs in inspect.getmembers(preset_class):
            if not permission_name.startswith("can_"):
                continue
            if not isinstance(permission_needs, (list, tuple)):
                continue
            yield permission_name, permission_needs

    @classmethod
    def _get_preset_classes(cls) -> List[Type[BasePermissionPolicy]]:
        """
        Returns a list of permission presets classes to be used for this service.

        The list is read from the configuration, if it exists, otherwise it returns
        the default value from the class attribute PERMISSIONS_PRESETS.
        """
        registered_preset_classes = current_app.config["OAREPO_PERMISSIONS_PRESETS"]
        preset_classes = []
        for x in cls._get_permissions_presets():
            if isinstance(x, str):
                preset_classes.append(registered_preset_classes[x])
            else:
                preset_classes.append(x)

        if hasattr(cls, "base_permission_policy_cls"):
            preset_classes.insert(0, cls.base_permission_policy_cls)
        return preset_classes

    @classmethod
    def _get_permissions_presets(cls):
        """
        Returns a list of names of permissions presets to be used for this service.

        The list is read from the configuration, if it exists, otherwise it returns
        the default value from the class attribute PERMISSIONS_PRESETS.
        """
        config_key = cls._get_presents_config_key()
        if config_key in current_app.config:
            return current_app.config[config_key]
        return (
            cls.PERMISSIONS_PRESETS
        )  # noqa (omitted here because of the order of mixins)

    @classmethod
    def _get_presents_config_key(cls):
        """
        Returns the name of the configuration key that contains the list of
        permissions presets to be used for this service.

        The key is read from the class attribute PERMISSIONS_PRESETS_CONFIG_KEY.
        If it is not set, the key is generated from the name of the service
        configuration class (MyServiceConfig becomes MY_SERVICE_PERMISSIONS_PRESETS).
        """
        if cls.PERMISSIONS_PRESETS_CONFIG_KEY:
            return cls.PERMISSIONS_PRESETS_CONFIG_KEY

        # use the base class of the service config file (e.g. MyServiceConfig),
        # remove the "Config" part and convert it to snake uppercase.
        # add "_PERMISSIONS_PRESETS" at the end.
        name = cls.__name__
        if name.endswith("Config"):
            name = name[:-6]
        name = re.sub(r"(?<!^)(?=[A-Z])", "_", name).upper()
        return f"{name}_PERMISSIONS_PRESETS"
