#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Tests for OARepoRuntime.login_user."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from flask import g, request
from flask_login import current_user
from flask_principal import UserNeed

import oarepo_runtime.ext as ext_module

if TYPE_CHECKING:
    from flask import Flask

    from oarepo_runtime.ext import OARepoRuntime


@pytest.fixture
def runtime_ext(app: Flask) -> OARepoRuntime:
    """Return the registered OARepoRuntime extension."""
    return app.extensions["oarepo-runtime"]


def test_login_user_sets_current_user_and_identity(app, runtime_ext, users):
    user = users[0]

    assert not current_user.is_authenticated

    with runtime_ext.login_user(user.email) as logged_in_user:
        assert logged_in_user.id == user.user.id
        assert logged_in_user.email == user.email
        assert current_user.is_authenticated
        assert current_user.id == user.user.id
        assert UserNeed(user.user.id) in g.identity.provides

    # logged out and identity cleared again once the block exits
    assert not current_user.is_authenticated
    assert g.identity.id is None


def test_login_user_reuses_active_request_context(app, runtime_ext, users):
    """When called while a request context is already active it must be reused.

    Nothing should be pushed/popped on top of it - the caller's context (e.g.
    a real web request) must be left untouched once the block exits.
    """
    user = users[0]

    with app.test_request_context("/some/path"):
        assert not current_user.is_authenticated

        with runtime_ext.login_user(user.email) as logged_in_user:
            assert logged_in_user.email == user.email
            assert current_user.is_authenticated
            # still the same (outer) request, not a newly pushed one
            assert request.path == "/some/path"

        # still the same outer request context, now logged out again
        assert not current_user.is_authenticated
        assert request.path == "/some/path"


def test_login_user_pushes_context_when_none_active(app, runtime_ext, users, monkeypatch):
    """Simulate CLI usage where no request context is active beforehand.

    The context manager must push a request context of its own so that
    Flask-Login/Flask-Principal have somewhere to store the identity, and pop
    it again once done.
    """
    monkeypatch.setattr(ext_module, "has_request_context", lambda: False)
    user = users[0]

    with runtime_ext.login_user(user.email) as logged_in_user:
        assert logged_in_user.email == user.email
        assert current_user.is_authenticated

    assert not current_user.is_authenticated


def test_login_user_unknown_email_raises_lookup_error(app, runtime_ext):
    with pytest.raises(LookupError), runtime_ext.login_user("does-not-exist@example.org"):
        pass  # pragma: no cover - must not be reached

    assert not current_user.is_authenticated


def test_login_user_logs_out_on_exception(app, runtime_ext, users):
    """The user must be logged out even if the body of the block raises."""
    user = users[0]

    class BoomError(Exception):
        pass

    with pytest.raises(BoomError), runtime_ext.login_user(user.email):
        raise BoomError

    assert not current_user.is_authenticated


def test_login_user_can_be_used_with_different_users_sequentially(app, runtime_ext, users):
    first, second = users[0], users[1]

    with runtime_ext.login_user(first.email) as logged_in:
        assert logged_in.id == first.user.id

    assert not current_user.is_authenticated

    with runtime_ext.login_user(second.email) as logged_in:
        assert logged_in.id == second.user.id
        assert logged_in.id != first.user.id

    assert not current_user.is_authenticated
