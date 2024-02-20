from typing import List

from flask import current_app
from invenio_records.systemfields import DictField, SystemField
from invenio_records_resources.services.custom_fields import BaseCF

from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin


class CustomFieldsMixin(MappingSystemFieldMixin):
    def __init__(self, config_key, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config_key = config_key

    @property
    def mapping(self):
        custom_fields: List[BaseCF] = current_app.config[self.config_key]
        return {cf.name: cf.mapping for cf in custom_fields}

    @property
    def mapping_settings(self):
        return {}

    def search_dump(self, data, record):
        custom_fields = current_app.config.get(self.config_key, {})

        for cf in custom_fields:
            cf.dump(data, cf_key=self.key)
        return data

    def search_load(self, data, record_cls):
        custom_fields = current_app.config.get(self.config_key, {})

        for cf in custom_fields:
            cf.load(data, cf_key=self.key)
        return data


class CustomFields(CustomFieldsMixin, DictField):
    @property
    def mapping(self):
        return {self.key: {"type": "object", "properties": super().mapping}}


class InlinedCustomFields(CustomFieldsMixin, SystemField):
    pass


class InlinedCustomFieldsSchemaMixin:
    CUSTOM_FIELDS_VAR = None
    CUSTOM_FIELDS_FIELD_PROPERTY = "field"

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        if self.CUSTOM_FIELDS_VAR is None:
            raise AttributeError(
                "CUSTOM_FIELDS_VAR field must be set to the name of config variable containing an array of custom fields"
            )
        custom_fields = current_app.config.get(self.CUSTOM_FIELDS_VAR, [])
        if not isinstance(custom_fields, (list, tuple)):
            raise AttributeError("CUSTOM_FIELDS_VAR must be a list or tuple")
        for cf in custom_fields:
            self.declared_fields[cf.name] = getattr(
                cf, self.CUSTOM_FIELDS_FIELD_PROPERTY
            )
        self._init_fields()


class InlinedUICustomFieldsSchemaMixin(InlinedCustomFieldsSchemaMixin):
    CUSTOM_FIELDS_FIELD_PROPERTY = "ui_field"
