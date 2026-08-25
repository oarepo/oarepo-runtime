#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""OARepo extensions to explain permissions."""

from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast, override

from invenio_records_permissions.generators import ConditionalGenerator, Generator, SameAs

from oarepo_runtime import current_runtime

if TYPE_CHECKING:
    from collections.abc import Collection

    from flask_principal import Identity, Need
    from invenio_records_permissions import RecordPermissionPolicy

type ExplainerResult = list[str | ExplainerResult]


class PermissionExplainer:
    """Protocol for permission explainers."""

    TYPES: ClassVar[tuple[type[Generator]]]

    def __init__(self, permission_policy: RecordPermissionPolicy, generator: Generator):
        """Initialize the explainer with the permission policy and generator."""
        self.permission_policy = permission_policy
        self.generator = generator

    @property
    def name(self) -> str:
        """Return the name of the generator."""
        return type(self.generator).__name__

    @property
    def needs(self) -> Collection[Need]:
        """Return the needs of the generator."""
        return cast("Collection[Need]", self.generator.needs(**self.permission_policy.over))

    def explain(self, identity: Identity) -> ExplainerResult:
        """Explain the permission generator."""
        icon, extra = self.icon(identity)
        try:
            needs = self.needs
        except Exception:  # noqa: BLE001
            needs = "<needs could not be computed>"
        r: ExplainerResult = [f"{icon} {self.name} {needs}"]
        if extra:
            r.append(f"  - {extra}")
        return r

    def icon(self, identity: Identity) -> tuple[str, str | None]:
        """Return the icon for the given allows value."""
        try:
            allows = self.allows(identity, self.generator)
        except Exception as e:  # noqa: BLE001
            return "⚠️", str(e)
        else:
            return "✅" if allows else "❌", None

    def allows(self, identity: Identity, generator: Generator) -> bool:
        """Check if the identity allows the permission generator."""

        class P(type(self.permission_policy)):  # type: ignore[misc]
            can_blah = (generator,)

        return cast("bool", P("blah", **self.permission_policy.over).allows(identity))


class DefaultExplainer(PermissionExplainer):
    """Default explainer that uses the permission generator's needs."""

    TYPES = (Generator,)


class ConditionalExplainer(PermissionExplainer):
    """Explainer that uses the permission generator's needs."""

    TYPES = (ConditionalGenerator,)

    @override
    def explain(self, identity: Identity) -> ExplainerResult:
        """Explain the permission generator."""
        generator = cast("ConditionalGenerator", self.generator)
        ret = list(super().explain(identity))
        condition_result = generator._condition(**self.permission_policy.over)  # noqa: SLF001
        sub_result: ExplainerResult = []
        if condition_result:
            sub_result.append("Then branch:")
            branch = generator.then_
        else:
            sub_result.append("Else branch:")
            branch = generator.else_

        for gen in branch:
            sub_result.append(explain(identity, self.permission_policy, gen))

        ret.append(sub_result)
        return ret


class SameAsExplainer(PermissionExplainer):
    """Explainer that uses the same explainer as the permission generator."""

    TYPES = (SameAs,)

    @property
    @override
    def name(self) -> str:
        generator = cast("SameAs", self.generator)
        return f"SameAs({generator._delegated_permission_name})"  # noqa: SLF001 # type: ignore[reportAttributeAccessIssue]

    @override
    def explain(self, identity: Identity) -> ExplainerResult:
        generator = cast("SameAs", self.generator)
        ret = super().explain(identity)
        for _gen in generator._generators(**self.permission_policy.over):  # noqa: SLF001
            ret.append(explain(identity, self.permission_policy, _gen))
        return ret


def explain(identity: Identity, policy: RecordPermissionPolicy, generator: Generator) -> ExplainerResult:
    """Explain the permission generators."""
    for explainer in current_runtime.explainers:
        if not isinstance(generator, explainer.TYPES):
            continue

        return explainer(policy, generator).explain(
            identity,
        )
    raise ValueError(f"Generator {generator} is not supported by any explainer")


def format_explanation(result: ExplainerResult, indent: str = "") -> str:
    """Format the explanation result as a string."""

    def result_to_list(result: ExplainerResult, indent: str) -> list[str]:
        ret = []
        for r in result:
            if isinstance(r, str):
                ret.append(indent + r)
            else:
                ret.extend(result_to_list(r, indent + "    "))
        return ret

    return "\n".join(result_to_list(result, indent))
