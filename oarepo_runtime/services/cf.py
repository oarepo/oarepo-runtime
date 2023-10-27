from invenio_records_resources.services.custom_fields.schema import (
    CustomFieldsSchemaUI as InvenioCustomFieldsSchemaUI,
)


class CustomFieldsSchemaUI(InvenioCustomFieldsSchemaUI):
    def _serialize(self, obj, **kwargs):
        self._schema.context.update(self.context)
        return super()._serialize(obj, **kwargs)

    def _deserialize(self, data, **kwargs):
        self._schema.context.update(self.context)
        return super()._deserialize(data, **kwargs)
