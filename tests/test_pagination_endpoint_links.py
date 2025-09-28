#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for pagination endpoint links."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Blueprint

from oarepo_runtime.services.records.links import (
    pagination_endpoint_links_html,
    rdm_pagination_record_endpoint_links,
)


@pytest.fixture(scope="module")
def app_with_blueprint(app):
    bp = Blueprint("pagination_test", __name__)

    @bp.route("/pagination_test/search")
    def search() -> str:
        return "search"  # pragma: no cover - used only for link generation

    @bp.route("/pagination_test/record_search/<pid_value>/versions")
    def record_search(pid_value) -> str:
        return "search"  # pragma: no cover - used only for link generation

    app.register_blueprint(bp)
    return app


def test_pagination_endpoint_links(app_with_blueprint):
    links = pagination_endpoint_links_html("pagination_test.search")
    pagination = SimpleNamespace(
        page=5,
        size=10,
        prev_page=SimpleNamespace(page=4),
        next_page=SimpleNamespace(page=6),
    )
    context = {"args": {"page": 5, "size": 10}}
    assert (
        links["prev_html"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/search?page=4&size=10"
    )
    assert (
        links["self_html"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/search?page=5&size=10"
    )
    assert (
        links["next_html"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/search?page=6&size=10"
    )


def test_pagination_rdm_record_endpoint_links(app_with_blueprint):
    #
    # rdm records scan uses pid_value parameter
    #
    links = rdm_pagination_record_endpoint_links("pagination_test.record_search")
    pagination = SimpleNamespace(
        page=3,
        size=10,
        prev_page=SimpleNamespace(page=2),
        next_page=SimpleNamespace(page=4),
    )
    context = {"args": {"page": 3, "size": 10}, "pid_value": "123"}
    assert (
        links["prev"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/record_search/123/versions?page=2&size=10"
    )
    assert (
        links["self"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/record_search/123/versions?page=3&size=10"
    )
    assert (
        links["next"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/record_search/123/versions?page=4&size=10"
    )


def test_pagination_rdm_record_endpoint_links_with_id(app_with_blueprint):
    #
    # draft records search uses id parameter
    #
    links = rdm_pagination_record_endpoint_links("pagination_test.record_search")
    pagination = SimpleNamespace(
        page=3,
        size=10,
        prev_page=SimpleNamespace(page=2),
        next_page=SimpleNamespace(page=4),
    )
    context = {"args": {"page": 3, "size": 10}, "id": "123"}
    assert (
        links["prev"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/record_search/123/versions?page=2&size=10"
    )
    assert (
        links["self"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/record_search/123/versions?page=3&size=10"
    )
    assert (
        links["next"].expand(pagination, context)
        == "https://127.0.0.1:5000/api/pagination_test/record_search/123/versions?page=4&size=10"
    )
