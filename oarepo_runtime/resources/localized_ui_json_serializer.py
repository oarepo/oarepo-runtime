import marshmallow
from flask_resources import MarshmallowSerializer

from oarepo_runtime.i18n import get_locale


class LocalizedUIJSONSerializer(MarshmallowSerializer):
    def __init__(
        self,
        format_serializer_cls,
        object_schema_cls,
        list_schema_cls=None,
        schema_context=None,
        **serializer_options,
    ):
        # the constructor instantiates the object_schema_cls, which is too early
        # if the schema uses current_app (for example, for translations or custom fields)
        # so we pass an empty schema and replace it later
        super().__init__(
            format_serializer_cls=format_serializer_cls,
            object_schema_cls=marshmallow.Schema,
            list_schema_cls=marshmallow.Schema,
            schema_context=schema_context or {},
            **serializer_options,
        )
        # replace the object schema class
        self.object_schema_cls = object_schema_cls
        self.list_schema_cls = list_schema_cls

    def dump_obj(self, obj):
        """Dump the object using object schema class."""
        return self.object_schema_cls(
            context={**self.schema_context, "locale": get_locale()}
        ).dump(obj)

    def dump_list(self, obj_list):
        """Dump the list of objects."""
        ctx = {
            "object_schema_cls": self.object_schema_cls,
        }
        ctx.update(self.schema_context)
        ctx["locale"] = get_locale()

        if self.list_schema_cls is None:
            return self.object_schema_cls(context=self.schema_context).dump(
                obj_list, many=True
            )

        return self.list_schema_cls(context=ctx).dump(obj_list)
