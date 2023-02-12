from invenio_records.systemfields import SystemField, DictField


class CustomFields(DictField):
    def __init__(self, config_key, key=None, clear_none=False, create_if_missing=True):
        super().__init__(
            key=key, clear_none=clear_none, create_if_missing=create_if_missing
        )
        self.config_key = config_key
