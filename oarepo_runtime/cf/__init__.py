from flask import current_app
from invenio_records.systemfields import DictField, SystemField


class CustomFieldsMixin:
    def __init__(self, config_key, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config_key = config_key


class CustomFields(CustomFieldsMixin, DictField):
    pass


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
