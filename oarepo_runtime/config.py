from typing import cast

from flask import Flask


def build_config[T: type](config_class: T, app: Flask) -> T:
    """
    Builds the configuration for the service

    This function is used to build the configuration for the service
    """
    if hasattr(config_class, "build") and callable(config_class.build):
        return cast(T, config_class.build(app))
    else:
        return config_class()
