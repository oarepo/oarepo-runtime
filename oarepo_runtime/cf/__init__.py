from invenio_records.systemfields import SystemField, DictField


class CustomFieldsMixin:
    def __init__(self, config_key, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.config_key = config_key


class CustomFields(CustomFieldsMixin, DictField):
    pass


class InlinedCustomFields(CustomFieldsMixin, SystemField):
    pass
