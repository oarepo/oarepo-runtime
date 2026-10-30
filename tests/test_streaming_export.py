# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT
"""Tests for streaming exports (Export.streaming)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from flask import Flask, Response
from signposting import LinkRel

from oarepo_runtime.api import Export, ExportEngine, ExportRepresentation
from oarepo_runtime.ext import OARepoRuntime
from oarepo_runtime.resources.signposting import landing_page_signpost_links_list

RECORD = {"$schema": "local://test.json", "id": "abc"}


class _StreamingSerializer:
    def __init__(self):
        self.calls = 0

    def serialize_object(self, obj):
        self.calls += 1
        return Response(iter([b"chunk-1", b"chunk-2"]), mimetype="application/zip")


class _JSONSerializer:
    def __init__(self):
        self.calls = 0

    def serialize_object(self, obj):
        self.calls += 1
        return '{"id": "abc"}'


@pytest.fixture
def exports():
    return {
        "zip": Export(
            code="zip",
            name="ZIP",
            mimetype="application/zip",
            serializer=_StreamingSerializer(),
            streaming=True,
        ),
        "json": Export(code="json", name="JSON", mimetype="application/json", serializer=_JSONSerializer()),
    }


@pytest.fixture
def runtime_app(exports):
    app = Flask("test")
    runtime = OARepoRuntime(app)
    model = SimpleNamespace(
        exports=list(exports.values()),
        ui_url=lambda view_name, pid_value, export_format: f"https://repo/records/{pid_value}/export/{export_format}",
        get_export_by_code=lambda code: exports.get(code),  # noqa: PLW0108 - called with code= keyword
        get_export_by_mimetype=lambda mimetype: next((e for e in exports.values() if e.mimetype == mimetype), None),
    )
    runtime.__dict__["models_by_schema"] = {"local://test.json": model}
    with app.app_context():
        yield runtime


def test_streaming_defaults_to_false():
    export = Export(code="json", name="JSON", mimetype="application/json", serializer=_JSONSerializer())
    assert export.streaming is False


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"export_code": "zip"}, None),
        ({"export_mimetype": "application/zip"}, None),
        ({"export_code": "missing"}, "No export found"),
        ({}, "both are None"),
        ({"export_code": "zip", "export_mimetype": "application/zip"}, "both are set"),
    ],
)
def test_get_export(runtime_app, exports, kwargs, message):
    if message is None:
        assert runtime_app.get_export(RECORD, **kwargs) is exports["zip"]
    else:
        with pytest.raises(ValueError, match=message):
            runtime_app.get_export(RECORD, **kwargs)


def test_streaming_export_as_response(runtime_app):
    body, status, headers = runtime_app.get_export_from_serialized_record(
        RECORD, representation=ExportRepresentation.RESPONSE, export_code="zip"
    )

    assert isinstance(body, Response)
    assert b"".join(body.response) == b"chunk-1chunk-2"
    assert status == 200
    assert headers == {"Content-Type": "application/zip", "Content-Disposition": "attachment; filename=abc.zip"}


@pytest.mark.parametrize("representation", [ExportRepresentation.DICTIONARY, ExportRepresentation.XML])
def test_streaming_export_rejects_other_representations(runtime_app, exports, representation):
    with pytest.raises(ValueError, match="'zip' is streaming"):
        runtime_app.get_export_from_serialized_record(RECORD, representation=representation, export_code="zip")
    # rejected before the (possibly expensive) serializer is invoked
    assert exports["zip"].serializer.calls == 0


def test_export_engine_does_not_cache_streaming_exports(runtime_app, exports):
    with ExportEngine.export_cache():
        first = ExportEngine.export(RECORD, export_code="zip", representation=ExportRepresentation.RESPONSE)
        second = ExportEngine.export(RECORD, export_code="zip", representation=ExportRepresentation.RESPONSE)

    assert first[0] is not second[0]
    assert exports["zip"].serializer.calls == 2


def test_export_engine_still_caches_regular_exports(runtime_app, exports):
    with ExportEngine.export_cache():
        first = ExportEngine.export(RECORD, export_code="json")
        second = ExportEngine.export(RECORD, export_code="json")

    assert first == second == {"id": "abc"}
    assert exports["json"].serializer.calls == 1


def test_signposting_skips_streaming_exports(runtime_app):
    links = landing_page_signpost_links_list({}, RECORD, short=False)

    assert [(link.rel, str(link.target)) for link in links if link.rel == LinkRel.describedby] == [
        (LinkRel.describedby, "https://repo/records/abc/export/json")
    ]
