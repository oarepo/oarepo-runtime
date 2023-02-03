class ExpandableFieldsConfigMixin:
    @property
    def expandable_fields(self):
        return getattr(self.config, "expandable_fields", [])
