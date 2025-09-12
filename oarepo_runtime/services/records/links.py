#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Utility for rendering URI template links."""

from __future__ import annotations

from invenio_records_resources.services.base.links import EndpointLink


def pagination_endpoint_links_html(endpoint: str, params: list[str] | None = None) -> dict[str, EndpointLink]:
    """Create pagination links (prev/self/next) from the same endpoint."""
    return {
        "prev_html": EndpointLink(
            endpoint,
            when=lambda pagination, _ctx: pagination.has_prev,
            vars=lambda pagination, _vars: _vars["args"].update({"page": pagination.prev_page.page}),
            params=params,
        ),
        "self_html": EndpointLink(endpoint, params=params),
        "next_html": EndpointLink(
            endpoint,
            when=lambda pagination, _ctx: pagination.has_next,
            vars=lambda pagination, _vars: _vars["args"].update({"page": pagination.next_page.page}),
            params=params,
        ),
    }
