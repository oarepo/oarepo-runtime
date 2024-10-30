from marshmallow import Schema, fields
from oarepo_runtime.services.schema.marshmallow_to_json_schema import marshmallow_to_json_schema

class SimpleSchema(Schema):
    a = fields.Integer()
    b = fields.String()

def test_simple_schema():
    schema = SimpleSchema()
    converted = marshmallow_to_json_schema(schema)

    assert converted == {
        "type": "object",
        "properties": {
            "a": {"type": "integer"},
            "b": {"type": "string"}
        }
    }

class AddressSchema(Schema):
    city = fields.String()
    postal_code = fields.String()

class MoreComplexSchema(Schema):
    name = fields.String(required=True)
    age = fields.Integer()
    score = fields.Float()
    is_active = fields.Boolean()
    tags = fields.List(fields.String())
    address = fields.Nested(lambda: AddressSchema)

def test_more_complex_schema():
    schema = MoreComplexSchema()
    converted = marshmallow_to_json_schema(schema)

    assert converted == {
        "type": "object",
        "properties": {
            'name': {'type': 'string'},
            'age': {'type': 'integer'},
            'score': {'type': 'number'},
            'is_active': {'type': 'boolean'},
            'tags': {'type': 'array', 'items': {'type': 'string'}},
            'address': {
                'type': 'object',
                "properties": {
                    'city': {'type': 'string'},
                    'postal_code': {'type': 'string'}
                }
            }
        }
    }
