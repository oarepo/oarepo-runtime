#
# Copyright (c) 2026 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Tests for pluggable authentication providers."""

from __future__ import annotations

import functools
from typing import TYPE_CHECKING

import pytest
from flask import Flask

from oarepo_runtime.errors import AuthExceptionGroup
from oarepo_runtime.ext import OARepoRuntime, api_finalize_app, finalize_app

if TYPE_CHECKING:
    from collections.abc import Callable

    from flask import Response


class RecordingAuthProvider:
    """Auth provider that returns a preconfigured result and records calls."""

    def __init__(self, username: object | None = None, exc: Exception | None = None) -> None:
        """Create the provider with a fixed authentication result."""
        self.username = username
        self.exc = exc
        self.before_request_calls = 0
        self.after_request_responses: list[Response] = []

    def before_request(self) -> object | None:
        """Return the preconfigured username/exception pair."""
        if self.exc:
            raise self.exc
        self.before_request_calls += 1
        return self.username

    def after_request(self, response: Response) -> Response | None:
        """Record the response and mark it with a header."""
        self.after_request_responses.append(response)
        response.headers.add("X-Auth-After-Request", str(id(self)))
        return response


def _make_app(*providers: RecordingAuthProvider) -> Flask:
    """Create a plain Flask app with the runtime extension and injected providers."""
    app = Flask("test-auth-providers")
    ext = OARepoRuntime(app)
    # pre-fill the cached property so no entry points are consulted
    ext.__dict__["auth_providers"] = list(providers)

    @app.route("/ping")
    def ping() -> str:
        return "pong"

    return app


def test_auth_providers_loaded_from_entry_points(monkeypatch):
    class DummyEntryPoint:
        name = "dummy"

        def load(self) -> type[RecordingAuthProvider]:
            return RecordingAuthProvider

    def fake_entry_points(group: str) -> list[DummyEntryPoint]:
        assert group == "oarepo.auth_providers"
        return [DummyEntryPoint()]

    monkeypatch.setattr("oarepo_runtime.ext.entry_points", fake_entry_points)

    ext = OARepoRuntime()
    providers = ext.auth_providers
    assert len(providers) == 1
    assert isinstance(providers[0], RecordingAuthProvider)

    # the property is cached, entry points are loaded only once
    assert ext.auth_providers is providers


def test_auth_providers_sorted_by_entry_point_name(monkeypatch):
    class DummyEntryPoint:
        def __init__(self, name: str) -> None:
            self.name = name

        def load(self) -> Callable[[], RecordingAuthProvider]:
            return lambda: RecordingAuthProvider(username=self.name)

    def fake_entry_points(group: str) -> list[DummyEntryPoint]:
        assert group == "oarepo.auth_providers"
        return [DummyEntryPoint("20-second"), DummyEntryPoint("30-third"), DummyEntryPoint("10-first")]

    monkeypatch.setattr("oarepo_runtime.ext.entry_points", fake_entry_points)

    providers = OARepoRuntime().auth_providers

    assert [provider.username for provider in providers] == ["10-first", "20-second", "30-third"]


def test_before_request_stops_after_first_successful_provider(monkeypatch):
    monkeypatch.setattr("oarepo_runtime.ext.login_user", lambda user: True)  # noqa: ARG005
    first = RecordingAuthProvider(username=object())
    second = RecordingAuthProvider(username=object())
    app = _make_app(first, second)

    response = app.test_client().get("/ping")

    assert response.status_code == 200
    assert first.before_request_calls == 1
    assert second.before_request_calls == 0


def test_before_request_allows_anonymous_when_no_provider_matches():
    first = RecordingAuthProvider()
    second = RecordingAuthProvider()
    app = _make_app(first, second)

    response = app.test_client().get("/ping")

    assert response.status_code == 200
    assert response.text == "pong"


def test_before_request_failure_followed_by_success_does_not_raise(monkeypatch):
    monkeypatch.setattr("oarepo_runtime.ext.login_user", lambda user: True)  # noqa: ARG005
    failing = RecordingAuthProvider(exc=ValueError("bad token"))
    succeeding = RecordingAuthProvider(username=object())
    app = _make_app(failing, succeeding)

    response = app.test_client().get("/ping")

    assert response.status_code == 200


def test_before_request_raises_group_with_all_collected_exceptions():
    exc1 = ValueError("bad token")
    exc2 = PermissionError("expired certificate")
    app = _make_app(
        RecordingAuthProvider(exc=exc1),
        RecordingAuthProvider(),
        RecordingAuthProvider(exc=exc2),
    )
    ext = app.extensions["oarepo-runtime"]

    with app.test_request_context("/ping"), pytest.raises(AuthExceptionGroup) as exc_info:
        ext.auth_before_request()

    assert exc_info.value.exceptions == (exc1, exc2)


def test_after_request_called_on_first_response_only(monkeypatch):
    monkeypatch.setattr("oarepo_runtime.ext.login_user", lambda user: True)  # noqa: ARG005
    # the second provider is not consulted during authentication ...
    first = RecordingAuthProvider(username=object())
    second = RecordingAuthProvider()
    app = _make_app(first, second)

    response = app.test_client().get("/ping")

    assert response.status_code == 200
    # ... but both get the after-request callback and can modify the response
    assert len(first.after_request_responses) == 1
    assert len(second.after_request_responses) == 0
    assert response.headers.getlist("X-Auth-After-Request") == [str(id(first))]


def test_request_passes_without_any_providers():
    app = _make_app()

    response = app.test_client().get("/ping")

    assert response.status_code == 200
    assert response.text == "pong"


def _register_other_hooks(
    app: Flask,
) -> tuple[Callable[[], None], Callable[[], None], Callable[[Response], Response]]:
    @app.before_request
    def other_before() -> None:
        return None

    @app.before_request
    def another_before() -> None:
        return None

    @app.after_request
    def other_after(response: Response) -> Response:
        return response

    return other_before, another_before, other_after


@pytest.mark.parametrize("finalize", [finalize_app, api_finalize_app])
def test_finalize_app_moves_runtime_hooks_first(finalize):
    app = Flask("test-finalize")
    other_before, another_before, other_after = _register_other_hooks(app)
    OARepoRuntime(app)

    # the runtime hooks were registered last
    assert app.before_request_funcs[None][-1].__qualname__ == "OARepoRuntime.auth_before_request"
    assert app.after_request_funcs[None][-1].__qualname__ == "OARepoRuntime.auth_after_request"

    finalize(app)

    assert app.before_request_funcs[None][0].__qualname__ == "OARepoRuntime.auth_before_request"
    assert app.after_request_funcs[None][0].__qualname__ == "OARepoRuntime.auth_after_request"
    # the relative order of the remaining hooks is preserved
    assert app.before_request_funcs[None][1:] == [other_before, another_before]
    assert app.after_request_funcs[None][1:] == [other_after]


def test_finalize_app_handles_hooks_without_qualname():
    app = Flask("test-finalize-partial")
    app.before_request(functools.partial(lambda: None))
    app.after_request(functools.partial(lambda response: response))
    OARepoRuntime(app)

    finalize_app(app)

    assert app.before_request_funcs[None][0].__qualname__ == "OARepoRuntime.auth_before_request"
    assert app.after_request_funcs[None][0].__qualname__ == "OARepoRuntime.auth_after_request"


def test_finalize_app_without_registered_hooks():
    app = Flask("test-finalize-empty")

    finalize_app(app)  # must not raise

    assert not app.before_request_funcs.get(None)
    assert not app.after_request_funcs.get(None)


def test_auth_hooks_registered_on_invenio_app(app):
    before_qualnames = [getattr(f, "__qualname__", "") for f in app.before_request_funcs.get(None, [])]
    after_qualnames = [getattr(f, "__qualname__", "") for f in app.after_request_funcs.get(None, [])]

    assert "OARepoRuntime.auth_before_request" in before_qualnames
    assert "OARepoRuntime.auth_after_request" in after_qualnames


def test_error_handler(app, monkeypatch, client, users):
    monkeypatch.setitem(
        app.extensions["oarepo-runtime"].__dict__,
        "auth_providers",
        [RecordingAuthProvider(exc=ValueError("tralala"))],
    )
    res = client.get("/")
    assert res.status_code == 401
    assert res.json["message"] == "Authentication failed."
