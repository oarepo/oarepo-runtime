import marshmallow as ma

from oarepo_runtime.services.schema.marshmallow import DictOnlySchema


class BSchema(DictOnlySchema):
    a = ma.fields.String()


class ASchema(DictOnlySchema):
    values = ma.fields.String()
    keys = ma.fields.Nested(BSchema)
    items = ma.fields.List(ma.fields.Nested(BSchema))


def test_full_schema():
    s = ASchema()
    value = {"values": "test", "keys": {"a": "b"}, "items": [{"a": "b"}]}
    assert s.dump(value) == value
    assert s.load(value) == value


def test_no_values():
    s = ASchema()
    value = {"keys": {"a": "b"}, "items": [{"a": "b"}]}
    assert s.dump(value) == value
    assert s.load(value) == value


def test_no_keys():
    s = ASchema()
    value = {"values": "test", "items": [{"a": "b"}]}
    assert s.dump(value) == value
    assert s.load(value) == value


def test_no_items():
    s = ASchema()
    value = {"values": "test", "keys": {"a": "b"}}
    assert s.dump(value) == value
    assert s.load(value) == value
