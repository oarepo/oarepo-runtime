#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for date facets."""

from __future__ import annotations

from oarepo_runtime.services.facets.utils import build_facet


def test_date_facet(app):
    facet = build_facet(
        [
            {
                "facet": "oarepo_runtime.services.facets.date.DateFacet",
                "path": "metadata.created",
                "label": "created",
            }
        ]
    )
    with app.app_context():
        loc_date = facet.localized_value_labels(["1996-10-12"], "cs")
        assert loc_date == {"1996-10-12": "12. 10. 1996"}

        loc_date = facet.localized_value_labels(["x"], "cs")
        assert loc_date == {"x": "«Error formatting value 'x'»"}

    facet = build_facet(
        [
            {
                "facet": "oarepo_runtime.services.facets.date.TimeFacet",
                "path": "metadata.created",
                "label": "created",
            }
        ]
    )
    with app.app_context():
        loc_date = facet.localized_value_labels(["23:30:15"], "en")
        assert loc_date == {"23:30:15": "11:30:15\u202fPM"}

    facet = build_facet(
        [
            {
                "facet": "oarepo_runtime.services.facets.date.DateTimeFacet",
                "path": "metadata.created",
                "label": "created",
            }
        ]
    )
    with app.app_context():
        loc_date = facet.localized_value_labels(["2025-09-23 15:42:10.123456"], "en")
        assert loc_date == {"2025-09-23 15:42:10.123456": "Sep 23, 2025, 3:42:10\u202fPM"}

    facet = build_facet(
        [
            {
                "facet": "oarepo_runtime.services.facets.date.EDTFFacet",
                "path": "metadata.created",
                "label": "created",
            }
        ]
    )
    with app.app_context():
        loc_date = facet.localized_value_labels(["2000"], "en")
        assert loc_date == {"2000": "2000"}

    facet = build_facet(
        [
            {
                "facet": "oarepo_runtime.services.facets.date.AutoDateHistogramFacet",
                "path": "metadata.created",
                "label": "created",
            }
        ]
    )
    assert facet.agg_type == "auto_date_histogram"
