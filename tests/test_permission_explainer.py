#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Tests for oarepo_runtime.services.permission_explainer."""

from __future__ import annotations

from typing import Any, override

import pytest
from flask_principal import Identity, Need, UserNeed
from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import ConditionalGenerator, Generator, SameAs

from oarepo_runtime.services.permission_explainer import (
    ConditionalExplainer,
    DefaultExplainer,
    SameAsExplainer,
    explain,
    format_explanation,
)

need_a = UserNeed(1)
need_b = UserNeed(2)


class AllowNeed(Generator):
    """Generator granting access to a single, fixed need."""

    def __init__(self, need: Need):
        """Initialize with the need to grant access."""
        self.need = need

    @override
    def needs(self, **kwargs: Any):
        return [self.need]


class BrokenGenerator(Generator):
    """Generator that always raises when its needs are evaluated."""

    @override
    def needs(self, **kwargs: Any):
        raise RuntimeError("boom")


class FlagCondition(ConditionalGenerator):
    """Conditional generator switching branch based on the `flag` kwarg."""

    @override
    def _condition(self, flag=False, **kwargs: Any) -> bool:
        return flag


class BrokenCondition(ConditionalGenerator):
    """Conditional generator whose condition always raises (e.g. missing record)."""

    @override
    def _condition(self, **kwargs: Any) -> bool:
        raise AttributeError("'NoneType' object has no attribute 'get'")


class SamplePolicy(RecordPermissionPolicy):
    """Permission policy exercising every generator type the explainers support."""

    can_read = (AllowNeed(need_a),)
    can_update = (AllowNeed(need_b),)
    can_delete = SameAs("can_update")
    can_broken = (BrokenGenerator(),)
    can_conditional = (FlagCondition(then_=[AllowNeed(need_a)], else_=[AllowNeed(need_b)]),)
    can_broken_conditional = (BrokenCondition(then_=[AllowNeed(need_a)], else_=[AllowNeed(need_b)]),)


@pytest.fixture
def identity_a():
    """Identity providing need_a only."""
    identity = Identity(1)
    identity.provides.add(need_a)
    return identity


@pytest.fixture
def identity_b():
    """Identity providing need_b only."""
    identity = Identity(2)
    identity.provides.add(need_b)
    return identity


def test_permission_explainer_name(app, db):
    policy = SamplePolicy("read")
    explainer = DefaultExplainer(policy, SamplePolicy.can_read[0])
    assert explainer.name == "AllowNeed"


def test_permission_explainer_needs(app, db):
    policy = SamplePolicy("read")
    explainer = DefaultExplainer(policy, SamplePolicy.can_read[0])
    assert list(explainer.needs) == [need_a]


def test_allows_true_when_identity_has_need(app, db, identity_a):
    policy = SamplePolicy("read")
    generator = SamplePolicy.can_read[0]
    explainer = DefaultExplainer(policy, generator)
    assert explainer.allows(identity_a, generator) is True


def test_allows_false_when_identity_lacks_need(app, db, identity_b):
    policy = SamplePolicy("read")
    generator = SamplePolicy.can_read[0]
    explainer = DefaultExplainer(policy, generator)
    assert explainer.allows(identity_b, generator) is False


def test_icon_allow_deny_and_error(app, db, identity_a, identity_b):
    policy = SamplePolicy("read")
    explainer = DefaultExplainer(policy, SamplePolicy.can_read[0])
    assert explainer.icon(identity_a) == ("✅", None)
    assert explainer.icon(identity_b) == ("❌", None)

    broken_explainer = DefaultExplainer(SamplePolicy("broken"), SamplePolicy.can_broken[0])
    icon, extra = broken_explainer.icon(identity_a)
    assert icon == "⚠️"
    assert extra == "boom"


def test_default_explainer_explain_allowed(app, db, identity_a):
    policy = SamplePolicy("read")
    result = DefaultExplainer(policy, SamplePolicy.can_read[0]).explain(identity_a)
    assert len(result) == 1
    assert result[0].startswith("✅ AllowNeed")
    assert str(need_a) in result[0]


def test_default_explainer_explain_denied(app, db, identity_b):
    policy = SamplePolicy("read")
    result = DefaultExplainer(policy, SamplePolicy.can_read[0]).explain(identity_b)
    assert len(result) == 1
    assert result[0].startswith("❌ AllowNeed")


def test_default_explainer_explain_survives_broken_generator(app, db, identity_a):
    """explain() must not raise even if the generator's needs() always raises.

    icon() already catches such exceptions and reports them via the "extra"
    line; explain() must not blow up when it separately needs the needs list
    for the header line.
    """
    policy = SamplePolicy("broken")
    result = DefaultExplainer(policy, SamplePolicy.can_broken[0]).explain(identity_a)
    assert result[0].startswith("⚠️ BrokenGenerator")
    assert len(result) == 2
    assert result[1] == "  - boom"


def test_sameas_explainer_name(app, db):
    policy = SamplePolicy("delete")
    explainer = SameAsExplainer(policy, SamplePolicy.can_delete)
    assert explainer.name == "SameAs(can_update)"


def test_sameas_explainer_delegates_to_target_permission(app, db, identity_a, identity_b):
    policy = SamplePolicy("delete")
    generator = SamplePolicy.can_delete

    allowed_result = SameAsExplainer(policy, generator).explain(identity_b)
    assert allowed_result[0].startswith("✅ SameAs(can_update)")
    delegated = allowed_result[-1]
    assert isinstance(delegated, list)
    assert delegated[0].startswith("✅ AllowNeed")

    denied_result = SameAsExplainer(policy, generator).explain(identity_a)
    assert denied_result[0].startswith("❌ SameAs(can_update)")
    assert denied_result[-1][0].startswith("❌ AllowNeed")


def test_conditional_explainer_then_branch(app, db, identity_a):
    policy = SamplePolicy("conditional", flag=True)
    generator = SamplePolicy.can_conditional[0]

    result = ConditionalExplainer(policy, generator).explain(identity_a)

    assert result[0].startswith("✅ FlagCondition")
    branch = result[-1]
    assert branch[0] == "Then branch:"
    sub_explain = branch[1]
    assert sub_explain[0].startswith("✅ AllowNeed")


def test_conditional_explainer_else_branch(app, db, identity_b):
    policy = SamplePolicy("conditional", flag=False)
    generator = SamplePolicy.can_conditional[0]

    result = ConditionalExplainer(policy, generator).explain(identity_b)

    assert result[0].startswith("✅ FlagCondition")
    branch = result[-1]
    assert branch[0] == "Else branch:"
    sub_explain = branch[1]
    assert sub_explain[0].startswith("✅ AllowNeed")


def test_conditional_explainer_survives_broken_condition(app, db, identity_a):
    """explain() must not raise even if the generator's _condition() always raises.

    This happens in practice e.g. when a generator expects a real record but
    the CLI is invoked without a record id, ending up with record=None.
    """
    policy = SamplePolicy("broken_conditional")
    generator = SamplePolicy.can_broken_conditional[0]

    result = ConditionalExplainer(policy, generator).explain(identity_a)

    warning = result[-1]
    assert isinstance(warning, list)
    assert warning[0].startswith("⚠️ Condition could not be evaluated")
    assert "NoneType" in warning[0]


def test_explain_dispatches_default_explainer(app, db, identity_a):
    policy = SamplePolicy("read")
    result = explain(identity_a, policy, SamplePolicy.can_read[0])
    assert result[0].startswith("✅ AllowNeed")


def test_explain_dispatches_sameas_explainer(app, db, identity_b):
    policy = SamplePolicy("delete")
    result = explain(identity_b, policy, SamplePolicy.can_delete)
    assert result[0].startswith("✅ SameAs(can_update)")


def test_explain_dispatches_conditional_explainer(app, db, identity_a):
    policy = SamplePolicy("conditional", flag=True)
    result = explain(identity_a, policy, SamplePolicy.can_conditional[0])
    assert result[0].startswith("✅ FlagCondition")


def test_explain_raises_for_unsupported_generator_type(app, db, identity_a):
    class NotAGenerator:
        pass

    policy = SamplePolicy("read")
    with pytest.raises(ValueError, match="is not supported by any explainer"):
        explain(identity_a, policy, NotAGenerator())


def test_format_explanation_flattens_nested_structure():
    result = [
        "✅ Foo",
        [
            "Then branch:",
            ["✅ Bar"],
        ],
    ]

    assert format_explanation(result) == "✅ Foo\n    Then branch:\n        ✅ Bar"


def test_format_explanation_applies_initial_indent():
    assert format_explanation(["✅ Foo"], indent="  ") == "  ✅ Foo"


def test_format_explanation_of_conditional_explain_result(app, db, identity_a):
    policy = SamplePolicy("conditional", flag=True)
    generator = SamplePolicy.can_conditional[0]
    result = ConditionalExplainer(policy, generator).explain(identity_a)

    formatted = format_explanation(result)

    lines = formatted.splitlines()
    assert lines[0].startswith("✅ FlagCondition")
    assert lines[1] == "    Then branch:"
    assert lines[2].strip().startswith("✅ AllowNeed")
    assert lines[2].startswith("        ")
