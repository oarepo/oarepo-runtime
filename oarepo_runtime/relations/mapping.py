class RelationsMapping:
    """Helper class for managing relation fields."""

    def __init__(self, record, fields):
        """Initialize the relations mapping."""
        # Needed because we overwrite __setattr__
        cache = {}
        self._fields = fields
        for name, fld in fields.items():
            field_value = fld.get_value(record, cache)
            setattr(self, name, field_value)

    def __iter__(self):
        """Iterate over the relations fields."""
        return iter(self._fields)

    def validate(self, fields=None):
        """Validates all relations in the record."""
        for name in fields or self:
            getattr(self, name).validate()

    def dereference(self, fields=None):
        """Dereferences relation fields."""
        for name in fields or self:
            getattr(self, name).dereference()

    def clean(self, fields=None):
        """Clean dereferenced relation fields."""
        for name in fields or self:
            getattr(self, name).clean()

    def set_cache(self, cache):
        from oarepo_runtime.relations import PIDRelation

        for key, fld in self._fields.items():
            if isinstance(fld, PIDRelation):
                fld.cache = cache
                getattr(self, key).cache = cache
