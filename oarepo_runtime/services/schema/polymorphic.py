from functools import cached_property

import marshmallow as ma

# from marshmallow_oneofschema import OneOfSchema
from oarepo_runtime.services.schema.oneofschema import OneOfSchema


class PolymorphicSchema(OneOfSchema):
    type_field_remove = False

    def get_obj_type(self, obj):
        return obj[self.type_field]

    @cached_property
    def type_schemas(self):
        ret = {}
        for key, fld in self.fields.items():
            if isinstance(fld, ma.fields.Nested):
                ret[fld.attribute or key] = type(fld.schema)
        return ret
