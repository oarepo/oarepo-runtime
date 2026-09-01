# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""OARepo Runtime package.

This package provides support for custom fields identification and iteration and `invenio oarepo cf init`
initialization tool for customfields.
"""

from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version

from .api import Model
from .ext import OARepoRuntime
from .proxies import current_runtime

try:
    __version__ = version("oarepo-runtime")
except PackageNotFoundError:
    __version__ = "0.0.0dev0+unknown"

__all__ = ("Model", "OARepoRuntime", "__version__", "current_runtime")
