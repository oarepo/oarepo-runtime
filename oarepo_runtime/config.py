from typing import Any, cast

from flask import Flask


def build_config[T: type](config_class: T, app: Flask, *args: Any, **kwargs: Any) -> T:
    """
    Builds the configuration for the service

    This function is used to build the configuration for the service
    """
    if hasattr(config_class, "build") and callable(config_class.build):
        if args or kwargs:
            raise ValueError(
                "Can not pass extra arguments when invenio ConfigMixin is used"
            )
        return cast(T, config_class.build(app))
    else:
        return config_class(*args, **kwargs)
