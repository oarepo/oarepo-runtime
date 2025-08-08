#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Config module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

if TYPE_CHECKING:
    from flask import Flask


def build_config[T: type](config_class: T, app: Flask, *args: Any, **kwargs: Any) -> Any:
    """Build the configuration for the service.

    This function is used to build the configuration for the service.
    """
    if hasattr(config_class, "build") and callable(config_class.build):
        if args or kwargs:
            raise ValueError("Can not pass extra arguments when invenio ConfigMixin is used")
        return cast("T", config_class.build(app))
    return config_class(*args, **kwargs)
