from invenio_records_resources.records.systemfields.relations import (
    PIDRelation,
    PIDListRelation,
    PIDNestedListRelation,
)
from invenio_records.dictutils import dict_lookup, dict_set

from invenio_records.systemfields.relations import (
    RelationResult,
    RelationListResult,
    RelationNestedListResult,
    RelationBase,
    ListRelation,
    NestedListRelation,
)


class MetadataRelationResultMixin:
    def _dereference_one(self, data, keys, attrs):
        ret = super()._dereference_one(data, keys, attrs)
        if "metadata" in ret:
            ret.update(ret.pop("metadata"))
        return ret


class MetadataRelationResult(MetadataRelationResultMixin, RelationResult):
    pass


class MetadataRelationListResult(MetadataRelationResultMixin, RelationListResult):
    pass


class MetadataRelationNestedListResult(
    MetadataRelationResultMixin, RelationNestedListResult
):
    pass


class MetadataPIDRelation(PIDRelation):
    result_cls = MetadataRelationResult


class MetadataPIDListRelation(PIDListRelation):
    result_cls = MetadataRelationListResult


class MetadataPIDNestedListRelation(PIDNestedListRelation):
    result_cls = MetadataRelationNestedListResult


from invenio_records.dictutils import dict_lookup, dict_set


class InternalResultMixin:
    def _lookup_id(self):
        return (super()._lookup_id(), self.record)

    def _dereference_one(self, data, keys, attrs):
        """Dereference a single object into a dict."""

        # Get related record
        obj = self.resolve((data[self.field._value_key_suffix], self.record))
        # Inject selected key/values from related record into
        # the current record.

        # From record dictionary
        if keys is None:
            data.update({k: v for k, v in obj.items()})
        else:
            new_obj = {}
            for k in keys:
                try:
                    val = dict_lookup(obj, k)
                    if val:
                        dict_set(new_obj, k, val)
                except KeyError:
                    pass
            data.update(new_obj)

        # From record attributes (i.e. system fields)
        for a in attrs:
            data[a] = getattr(obj, a)

        return data


class InternalResult(InternalResultMixin, RelationResult):
    pass


class InternalRelation(RelationBase):
    result_cls = InternalResult

    def __init__(self, *args, pid_field=None, **kwargs):
        """Initialize the PK relation."""
        self.pid_field = pid_field
        super().__init__(*args, **kwargs)

    def resolve(self, id_):
        pid_field = self.pid_field
        if not id_:
            return None

        if not pid_field:
            return id_[1]

        field_or_array = dict_lookup(id_[1], pid_field)
        if not field_or_array:
            return None

        if isinstance(field_or_array, dict):
            field_or_array = [field_or_array]
        if not isinstance(field_or_array, list):
            raise KeyError(
                f"PID field {pid_field} does not point to an object or array of objects"
            )
        for f in field_or_array:
            if not isinstance(f, dict):
                raise KeyError(
                    f"PID field {pid_field} does not point to an array of objects - array member is {type(f)}: {f}"
                )
            if id_[0] == f.get("id", None):
                return f
        return None


class InternalListResult(InternalResultMixin, RelationListResult):
    def _lookup_id(self, data):
        return (dict_lookup(data, self.field._value_key_suffix), self.record)


class InternalListRelation(ListRelation, InternalRelation):
    result_cls = InternalListResult


class InternalNestedListResult(InternalResultMixin, RelationNestedListResult):
    def _lookup_id(self, data):
        return (dict_lookup(data, self.field._value_key_suffix), self.record)


class InternalNestedListRelation(NestedListRelation, InternalRelation):
    result_cls = InternalNestedListResult
