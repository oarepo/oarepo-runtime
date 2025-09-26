#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Test export to response handlers conversion."""

from __future__ import annotations

from flask_resources.responses import ResponseHandler
from invenio_records_resources.resources.records.headers import etag_headers

from oarepo_runtime.resources.config import exports_to_response_handlers
from tests.conftest import _export


def test_exports_to_response_handlers_empty_iterable_returns_empty_dict():
    result = exports_to_response_handlers([])
    assert result == {}


def test_exports_to_response_handlers_maps_mimetypes_and_attributes():
    e1 = _export("code1", "application/x-test-1")
    e2 = _export("code2", "application/x-test-2")

    result = exports_to_response_handlers([e1, e2])

    # Keys map to mimetypes
    assert set(result.keys()) == {e1.mimetype, e2.mimetype}

    # Each value is a ResponseHandler with the correct serializer and headers
    h1 = result[e1.mimetype]
    h2 = result[e2.mimetype]

    assert isinstance(h1, ResponseHandler)
    assert isinstance(h2, ResponseHandler)

    # Serializer is passed through unmodified
    assert h1.serializer is e1.serializer
    assert h2.serializer is e2.serializer

    # Headers are the etag_headers callable from invenio
    assert h1.headers is etag_headers
    assert h2.headers is etag_headers


def test_exports_to_response_handlers_accepts_generators_as_iterable():
    def gen():  # noqa
        """Provide a generator of exports."""
        yield _export("g1", "application/x-gen-1")
        yield _export("g2", "application/x-gen-2")

    result = exports_to_response_handlers(gen())

    assert set(result.keys()) == {"application/x-gen-1", "application/x-gen-2"}
    for mt in result:
        assert isinstance(result[mt], ResponseHandler)
        assert result[mt].headers is etag_headers
