import marshmallow as ma
import pytest

from oarepo_runtime.services.schema import PolymorphicSchema


class SchemaA(ma.Schema):
    t = ma.fields.String()
    a = ma.fields.String()


class SchemaB(ma.Schema):
    t = ma.fields.String()
    b = ma.fields.String()


class PSchema(PolymorphicSchema):
    type_field = "t"
    a = ma.fields.Nested(SchemaA)
    b = ma.fields.Nested(SchemaB)


def test_polymorphic_schema():
    assert PSchema().load({"t": "a", "a": "aa"}) == {"t": "a", "a": "aa"}
    assert PSchema().load({"t": "b", "b": "bb"}) == {"t": "b", "b": "bb"}
    with pytest.raises(
        ma.exceptions.ValidationError, match=r"'a': \['Unknown field.'\]"
    ):
        assert PSchema().load({"t": "b", "a": "aa"})

    assert PSchema().dump({"t": "a", "a": "aa"}) == {"t": "a", "a": "aa"}
    assert PSchema().dump({"t": "b", "b": "bb"}) == {"t": "b", "b": "bb"}
