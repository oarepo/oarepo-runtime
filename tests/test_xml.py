# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT
from __future__ import annotations

from types import SimpleNamespace

import pytest
from lxml import etree
from marshmallow import ValidationError

from oarepo_runtime.api import ExportRepresentation
from oarepo_runtime.ext import OARepoRuntime
from oarepo_runtime.resources.xml import XMLDeserializer, XMLSerializer, parse_xml


@pytest.mark.parametrize("data", ["<a><b>č</b></a>", "<a><b>č</b></a>".encode()])
def test_parse_xml(data):
    element = parse_xml(data)
    assert element.tag == "a"
    assert element.findtext("b") == "č"


def test_parse_xml_invalid():
    with pytest.raises(ValidationError, match="Invalid XML"):
        parse_xml("<a><b></a>")


def test_parse_xml_does_not_expand_external_entities(tmp_path):
    secret = tmp_path / "secret.txt"
    secret.write_text("top-secret")
    data = f'<!DOCTYPE a [<!ENTITY x SYSTEM "file://{secret}">]><a>&x;</a>'

    element = parse_xml(data)

    assert "top-secret" not in etree.tostring(element, encoding=str)


def test_parse_xml_does_not_expand_internal_entities():
    data = '<!DOCTYPE a [<!ENTITY x "expanded">]><a>&x;</a>'

    element = parse_xml(data)

    assert "expanded" not in etree.tostring(element, encoding=str)


class _ElementSerializer:
    def serialize_object(self, obj):
        raise AssertionError("string serialization must not be used for the XML representation")

    def serialize_object_xml(self, obj):
        element = etree.Element("record")
        element.text = obj["id"]
        return element


class _StringSerializer:
    def serialize_object(self, obj):
        return f"<record>{obj['id']}</record>"


class _ElementDeserializer:
    def deserialize_xml(self, element):
        return {"id": element.text}


def test_protocols():
    assert isinstance(_ElementSerializer(), XMLSerializer)
    assert not isinstance(_StringSerializer(), XMLSerializer)
    assert isinstance(_ElementDeserializer(), XMLDeserializer)
    assert not isinstance(_StringSerializer(), XMLDeserializer)


@pytest.mark.parametrize("serializer", [_ElementSerializer(), _StringSerializer()])
def test_xml_export_representation(serializer):
    export = SimpleNamespace(serializer=serializer, streaming=False)
    model = SimpleNamespace(get_export_by_code=lambda code: export)
    runtime = OARepoRuntime()
    runtime.__dict__["models_by_schema"] = {"local://test.json": model}

    element = runtime.get_export_from_serialized_record(
        {"$schema": "local://test.json", "id": "abc"},
        representation=ExportRepresentation.XML,
        export_code="xml",
    )

    assert element.tag == "record"
    assert element.text == "abc"
