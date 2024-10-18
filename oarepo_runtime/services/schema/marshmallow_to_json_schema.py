from marshmallow import Schema, fields
from oarepo_runtime.services.schema.ui import LocalizedEDTFTime

field_type_converters = {
    fields.String : lambda field: {"type" : "string"},
    fields.Integer: lambda field: {"type": "integer"},
    fields.Float: lambda field: {"type": "number"},
    fields.Boolean: lambda field: {"type": "boolean"},
    fields.List: lambda field: {
        "type": "array",
        "items": convert_field_to_json_schema(field.inner)
    },
    fields.Nested: lambda field: {
        "type": "object",
        "properties": marshmallow_to_json_schema(field.schema)["properties"]
    },
    LocalizedEDTFTime: lambda field: {
        "type": "string",
        "format": "date-time",
    }
    # TODO raw fields?
    # TODO other date fields
}


def marshmallow_to_json_schema(schema:Schema) -> dict:
    json_schema = {
        'type': 'object',
        'properties': {}
    }

    for field_name, field in schema.fields.items():
        json_schema["properties"][field_name] = convert_field_to_json_schema(field)

    return json_schema


def convert_field_to_json_schema(field:fields) -> dict:
    for field_type in type(field).mro():
        if field_type in field_type_converters:
            return field_type_converters[field_type](field)

    # no converter found, just string
    return {"type":"string"}