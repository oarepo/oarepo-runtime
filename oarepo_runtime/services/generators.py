#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Typed invenio generators."""

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, override

from invenio_records_permissions.generators import (
    ConditionalGenerator as InvenioConditionalGenerator,
)
from invenio_records_permissions.generators import Generator as InvenioGenerator

if TYPE_CHECKING:
    from collections.abc import Sequence

    from flask_principal import Need
    from invenio_records_resources.records.api import Record
    from invenio_search.engine import dsl


class Generator(InvenioGenerator):
    """Custom generator for the service.

    This class will be removed when invenio has proper type stubs.
    """

    @override
    def needs(self, **kwargs: Any) -> Sequence[Need]:  # type: ignore[reportIncompatibleMethodOverride]
        return super().needs(**kwargs)  # type: ignore[no-any-return]

    @override
    def excludes(self, **kwargs: Any) -> Sequence[Need]:  # type: ignore[reportIncompatibleMethodOverride]
        return super().excludes(**kwargs)  # type: ignore[no-any-return]

    @override
    def query_filter(self, **kwargs: Any) -> dsl.query.Query:  # type: ignore[reportIncompatibleMethodOverride]
        return super().query_filter(**kwargs)  # type: ignore[no-any-return]


class ConditionalGenerator(InvenioConditionalGenerator):
    """Typed conditional generator.

    This class will be removed when invenio has proper type stubs.
    """

    def __init__(self, then_: Sequence[InvenioGenerator], else_: Sequence[InvenioGenerator]) -> None:
        """Initialize the conditional generator."""
        super().__init__(then_=then_, else_=else_)

    @abstractmethod
    def _condition(self, **kwargs: Any) -> bool:
        """Condition to choose generators set."""
        raise NotImplementedError  # pragma: nocover

    def _generators(self, record: Record, **kwargs: Any) -> Sequence[InvenioGenerator]:
        """Get the "then" or "else" generators."""
        return super()._generators(record=record, **kwargs)  # type: ignore[no-any-return]

    @override
    def needs(self, **kwargs: Any) -> Sequence[Need]:  # type: ignore[override]
        return super().needs(**kwargs)  # type: ignore[no-any-return]

    @override
    def excludes(self, **kwargs: Any) -> Sequence[Need]:  # type: ignore[override]
        return super().excludes(**kwargs)  # type: ignore[no-any-return]

    @override
    def query_filter(self, **kwargs: Any) -> dsl.query.Query:  # type: ignore[reportIncompatibleMethodOverride]
        return super().query_filter(**kwargs)  # type: ignore[no-any-return]
