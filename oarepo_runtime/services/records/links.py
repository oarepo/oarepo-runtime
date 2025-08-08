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

from invenio_records_resources.services.base.links import Link


def pagination_links_html(tpl: str) -> dict[str, Link]:
    """Create pagination links (prev/self/next) from the same template."""
    return {
        "prev_html": Link(
            tpl,
            when=lambda pagination: pagination.has_prev,
            vars=lambda pagination, variables: variables["args"].update({"page": pagination.prev_page.page}),
        ),
        "self_html": Link(tpl),
        "next_html": Link(
            tpl,
            when=lambda pagination: pagination.has_next,
            vars=lambda pagination, variables: variables["args"].update({"page": pagination.next_page.page}),
        ),
    }
