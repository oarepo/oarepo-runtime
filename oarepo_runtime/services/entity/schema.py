from marshmallow import Schema, fields


#
# The default record schema
#
class KeywordEntitySchema(Schema):
    keyword = fields.Str()
    id = fields.Str()
