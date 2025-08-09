from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

import pytest

from oarepo_runtime.config import build_config

if TYPE_CHECKING:
    from flask import Flask


def test_build_config(app: Flask) -> None:
    @dataclass(kw_only=True)
    class ConfigWithoutBuild:
        a: int

    class ConfigWithBuild:
        @classmethod
        def build(cls, app: Flask) -> str:  # noqa: ARG003 unused argument
            """Build configuration."""
            return "built!"

    c = build_config(ConfigWithoutBuild, app, a=1)
    assert c.a == 1

    d = build_config(ConfigWithBuild, app)
    assert d == "built!"

    with pytest.raises(ValueError, match="Can not pass extra arguments"):
        build_config(ConfigWithBuild, app, a=1)
