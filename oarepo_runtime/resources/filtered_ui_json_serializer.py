from oarepo_runtime.resources import LocalizedUIJSONSerializer

from oarepo_runtime.services.schema.filtered_ui_list_schema import FilteredUIListSchema


class FilteredUIJSONSerializer(LocalizedUIJSONSerializer):
    """UI JSON serializer."""

    def __init__(self, **kwargs):
        """Initialise Serializer."""

        super().__init__(
            **{
                **kwargs,
                "list_schema_cls": FilteredUIListSchema,
            }
        )
