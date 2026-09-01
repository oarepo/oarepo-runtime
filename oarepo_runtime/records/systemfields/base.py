# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Base typed system field implementation."""

from __future__ import annotations

from typing import Any, Self, overload

from invenio_records.api import Record
from invenio_records.extensions import ExtensionMixin
from invenio_records.systemfields import SystemField


class TypedSystemField[R: Record = Record, V: Any = Any](SystemField, ExtensionMixin):
    """Base class for typed system fields."""

    @overload
    def __get__(self, instance: None, owner: type[R]) -> Self: ...

    @overload
    def __get__(self, instance: R, owner: type[R]) -> V: ...

    def __get__(self, instance: R | None, owner: type[R]) -> Self | V:  # ty: ignore[invalid-method-override]
        """Get the value of the field."""
        if instance is None:  # pragma: no cover
            return self  # pragma: no cover
        raise NotImplementedError  # pragma: no cover

    @overload
    def __set__(self, instance: None, value: Self) -> None: ...

    @overload
    def __set__(self, instance: R, value: V) -> None: ...

    def __set__(self, instance: R | None, value: V | Self) -> None:  # ty: ignore[invalid-method-override]
        """Set the value of the field."""
        if instance is None:  # pragma: no cover
            raise ValueError("Cannot set value on class.")  # pragma: no cover
        raise NotImplementedError  # pragma: no cover
