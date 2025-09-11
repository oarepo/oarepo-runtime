#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test typing module."""

from __future__ import annotations

from typing import Any

import pytest

from oarepo_runtime.typing import require_kwargs


class A:
    """A."""

    @require_kwargs("bla")
    def whatever(self, *args: Any, **kwargs: Any) -> None:
        """Do nothing."""


def test_require_kwargs():
    a = A()
    a.whatever(bla=1)
    with pytest.raises(ValueError, match=r"Keyword argument bla not found in function call."):
        a.whatever(blb=1)
