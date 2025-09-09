#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""OARepo Runtime package.

This package provides support for custom fields identification and iteration and `invenio oarepo cf init`
initialization tool for customfields.
"""

from __future__ import annotations

from .api import Model
from .ext import OARepoRuntime
from .proxies import current_runtime

__version__ = "2.0.0dev17"

__all__ = ("Model", "OARepoRuntime", "__version__", "current_runtime")
