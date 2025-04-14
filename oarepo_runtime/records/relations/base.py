from functools import cached_property
from typing import List

from invenio_records.dictutils import dict_lookup, dict_set
from invenio_records.systemfields.base import SystemField
from invenio_records.systemfields.relations import (
    InvalidCheckValue,
    InvalidRelationValue,
)

from oarepo_runtime.services.relations.errors import MultipleInvalidRelationErrors
from oarepo_runtime.services.relations.mapping import RelationsMapping

from .lookup import LookupResult, lookup_key


class RelationResult:
    def __init__(self, field, record, cache) -> None:
        self.field = field
        self.record = record
        self.cache = cache

    def validate(self, raise_first_exception=True):
        found: List[LookupResult] = lookup_key(self.record, self.field.key)
        exceptions = []
        for relation in found:
            try:
                resolved_object = self._resolve_lookup_result(relation)

                if self.field.value_check:
                    transformed_data = {}
                    self._get_dereferenced_value(
                        transformed_data, resolved_object, relation
                    )
                    self._value_check(relation.value, transformed_data)
            except Exception as e:
                if raise_first_exception:
                    raise
                exceptions.append((relation, e))
        if exceptions:
            raise MultipleInvalidRelationErrors(exceptions)

    def _resolve_lookup_result(self, relation):
        if not isinstance(relation.value, dict):
            raise InvalidRelationValue(
                f"Value at path {relation.path} must be dict, found {relation.value}"
            )
        relation_id = self._lookup_id(relation)
        resolved_object = self.resolve(relation_id)
        if resolved_object is None:
            raise InvalidRelationValue(f"Could not resolve relation id {relation_id}.")
        return resolved_object

    def clean(self):
        """Clean the dereferenced attributes inside the record."""
        found: List[LookupResult] = lookup_key(self.record, self.field.key)
        for relation in found:
            self._clean_one(relation)

    def dereference(self):
        """Dereference the relation field object inside the record."""
        found: List[LookupResult] = lookup_key(self.record, self.field.key)
        for relation in found:
            self._dereference_one(relation)

    def _clean_one(self, relation: LookupResult):
        """
        Cleans the relation. The default implementation does nothing - the relation has been
        validated,
        """

    def _needs_update_relation_value(self, _relation: LookupResult):
        """
        Returns True if the relation needs resolving and updating value

        :param relation: relation being processed
        """
        return True

    def _add_version_info(self, data, relation: LookupResult, resolved_object):
        """
        Adds versioning info on relation data

        :param data: relation data
        :param relation: relation being processed
        :param resolved_object: the object to which this relation points to
        """

    def _dereference_one(self, relation: LookupResult):
        """Dereference a single object into a dict."""
        if not self._needs_update_relation_value(relation):
            return

        data = relation.value
        obj = self._resolve_lookup_result(relation)
        self._get_dereferenced_value(data, obj, relation)

        return data

    def _get_dereferenced_value(self, data, obj, relation):
        # Inject selected key/values from related record into
        # the current record.

        # From record dictionary
        if self.field.keys is None:
            data.update({k: v for k, v in obj.items()})
        else:
            new_obj = {}
            for k in self.field.keys:
                try:
                    key = self._get_dereference_key(k, relation)
                    target = self._get_dereference_target(k, relation)
                    val = dict_lookup(obj, key)
                    if val:
                        dict_set(new_obj, target, val)
                except KeyError:
                    pass
            data.update(new_obj)

        # From record attributes (i.e. system fields)
        for a in self.field.attrs:
            data[a] = getattr(obj, a)

        self._add_version_info(data, relation, obj)

    def _get_dereference_key(self, key, _relation: LookupResult):
        if isinstance(key, dict):
            return key["key"]
        return key

    def _get_dereference_target(self, key, _relation: LookupResult):
        if isinstance(key, dict):
            return key["target"]
        return key

    def _value_check(self, value_to_check, object):
        """Checks if the value is present in the object."""
        # TODO: this is way too complicated, should refactor it (and look at the code coverage as well)
        for key, value in value_to_check.items():
            if key not in object:
                raise InvalidCheckValue(f"Invalid key {key}.")
            if isinstance(value, dict):
                self._value_check(value, object[key])
            else:
                if not isinstance(value, list):
                    raise InvalidCheckValue(
                        f"Invalid value_check value: {value}; it must be " "a list"
                    )
                elif isinstance(object[key], list):
                    value_exist = set(object[key]).intersection(set(value))
                    if not value_exist:
                        raise InvalidCheckValue(
                            f"Failed cross checking value_check value "
                            f"{value} with record value {object[key]}."
                        )
                else:
                    if object[key] not in value:
                        raise InvalidCheckValue(
                            f"Failed cross checking value_check value "
                            f"{value} with record value {object[key]}."
                        )

    def _lookup_id(self, relation: LookupResult):
        relation_id = relation.value.get("id", None)
        if not relation_id:
            raise InvalidRelationValue(
                f"Value at path {relation.path} must contain non-empty 'id' field, found {relation.value}"
            )
        return relation_id

    def _store_id(self, relation: LookupResult, relation_id):
        relation.value["id"] = relation_id

    def resolve(self, id_):
        raise NotImplementedError("Please implement this method in your subclass")


class UnstrictRelationResult(RelationResult):

    def _resolve_lookup_result(self, relation):
        if not isinstance(relation.value, dict):
            raise InvalidRelationValue(
                f"Value at path {relation.path} must be dict, found {relation.value}"
            )
        if "id" not in relation.value:
            return relation.value
        relation_id = self._lookup_id(relation)
        resolved_object = self.resolve(relation_id, relation.value)
        if resolved_object is None:
            raise InvalidRelationValue(f"Could not resolve relation id {relation_id}.")
        return resolved_object

    def _dereference_one(self, relation: LookupResult):
        """Dereference a single object into a dict."""
        if not self._needs_update_relation_value(relation):
            return

        data = relation.value
        obj = self._resolve_lookup_result(relation)
        if type(obj) is not dict:
            self._get_dereferenced_value(data, obj, relation)

        return data


class Relation:
    result_cls = RelationResult

    def __init__(
        self,
        key=None,
        attrs=None,
        keys=None,
        _clear_empty=True,
        value_check=None,
    ):
        """Initialize the relation."""
        self.key = key
        self.attrs = attrs or []
        self.keys = keys or []
        self._clear_empty = _clear_empty
        self.value_check = value_check

    def get_value(self, record, cache):
        """Return the resolved relation from a record."""
        return self.result_cls(self, record, cache)


class RelationsField(SystemField):
    # taken from RelationsField
    def __init__(self, **fields):
        """Initialize the field."""
        super().__init__()
        assert all(isinstance(f, Relation) for f in fields.values())
        self._original_fields = fields

    def __getattr__(self, name):
        """Get a field definition."""
        if name in self._fields:
            return self._fields[name]
        raise AttributeError

    def __iter__(self):
        """Iterate over the configured fields."""
        return iter(getattr(self, f) for f in self._fields)

    def __contains__(self, name):
        """Return if a field exists in the configured fields."""
        return name in self._fields

    #
    # Properties
    #
    @cached_property
    def _fields(self):
        """Get the fields."""
        return self._original_fields

    #
    # Helpers
    #
    def obj(self, instance):
        """Get the relations object."""
        # Check cache
        obj = self._get_cache(instance)
        if obj:
            return obj
        obj = RelationsMapping(record=instance, fields=self._fields)
        self._set_cache(instance, obj)
        return obj

    #
    # Data descriptor
    #
    def __get__(self, record, owner=None):
        """Accessing the attribute."""
        # Class access
        if record is None:
            return self
        return self.obj(record)

    def __set__(self, instance, values):
        """Setting the attribute."""
        obj = self.obj(instance)
        for k, v in values.items():
            setattr(obj, k, v)

    #
    # Record extension
    #
    def pre_commit(self, record):
        """Initialise the model field."""
        obj = self.obj(record)
        obj.validate()
        obj.clean()
        obj.dereference()
