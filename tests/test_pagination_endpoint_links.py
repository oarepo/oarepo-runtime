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

from oarepo_runtime.services.records.links import pagination_endpoint_links_html


@pytest.fixture(scope="module")
def app_with_blueprint(app):
    bp = Blueprint("pagination_test", __name__)

    @bp.route("/pagination_test/search")
    def search() -> str:
        return "search"

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
