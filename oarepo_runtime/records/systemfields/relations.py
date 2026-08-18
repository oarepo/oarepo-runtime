#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""A relation field that resolves via an arbitrary path in the record, optionally through nested lists."""

from __future__ import annotations
from functools import cached_property

from itertools import zip_longest
from typing import TYPE_CHECKING, Any, override

from invenio_records.dictutils import dict_lookup, dict_set
from invenio_records.systemfields import SystemField
from invenio_records.systemfields.relations import (
    InvalidRelationValue,
    ListRelation,
    RelationListResult,
)
from invenio_records_resources.records.systemfields.relations import (
    PIDRelation,
)
from marshmallow import ValidationError

if TYPE_CHECKING:
    from collections.abc import Callable, Generator, Iterator

    from invenio_records.api import Record


class ArbitraryPathResult(RelationListResult):
    """Relation access result."""

    @override
    def __call__(self, force: bool = True):
        """Resolve the relation."""
        try:
            levels = len(self.field.path_elements)
            data = self._lookup_data()
            if levels == 0:
                # no array levels: resolve directly to a single object (or None),
                # not an iterator of objects
                if data is None:
                    return None
                return self.resolve(data[self._value_key_suffix])
            # not as efficient as it could be as we create the list of lists first
            # before returning the iterator, but simpler to implement
            return iter(
                _for_each_deep(
                    data,
                    lambda v: self.resolve(v[self._value_key_suffix]),
                    levels=levels,
                )
            )
        except KeyError:
            return None

    def _lookup_data(self) -> Any:
        """Lookup the data from the record."""

        # recursively lookup the data following the path elements. The end of the path
        # must always be an array of objects.
        def _lookup(r: Any, paths: list[str]) -> Any:
            if not paths:
                if self.field.relation_field:
                    try:
                        return dict_lookup(r, self.field.relation_field)
                    except KeyError:  # pragma: no cover
                        return None
                return r
            try:
                level_values = dict_lookup(r, paths[0])
                if not isinstance(level_values, list):
                    raise InvalidRelationValue(  # pragma: no cover
                        f'Invalid structure, expecting list at "{paths[0]}", got {level_values}. '
                        f'Complete paths: "{self.field.path_elements}"'
                    )
                ret = [_lookup(v, paths[1:]) for v in level_values]
                return [v for v in ret if v is not None]
            except KeyError:
                return []

        return _lookup(self.record, self.field.path_elements)

    @override
    def validate(self) -> None:
        """Validate the field."""
        try:
            values = self._lookup_data()
            # not as efficient as it could be as we create the list of lists first
            # before returning, but simpler to implement
            _for_each_deep(
                values,
                self._validate_single_value,
                levels=len(self.field.path_elements),
            )
        except KeyError:  # pragma: no cover
            return

    def _validate_single_value(self, v: Any) -> None:
        """Validate a single value."""
        if isinstance(v, list):
            raise InvalidRelationValue(f"Invalid value {v}, should not be list.")
        relation_id = self._lookup_id(v)
        if not self.exists(relation_id):
            raise InvalidRelationValue(f"Invalid value {relation_id}.")
        if self.value_check:  # pragma: no cover # not testing, copied from invenio
            obj = self.resolve(v[self.field._value_key_suffix])  # noqa: SLF001 # private attr
            self._value_check(self.value_check, obj)

    @override
    def _apply_items(  # type: ignore[override]
        self,
        func: Callable,
        keys: list[str] | None = None,
        attrs: list[str] | None = None,
    ) -> Any:
        """Iterate over the list of objects.

        Returns None on KeyError, func's result directly for a scalar (no array
        levels) relation, or a, possibly nested, list of func's results otherwise.
        """
        # The attributes we want to get from the related record.
        attrs = attrs or self.attrs
        keys = keys or self.keys
        try:
            # Get the list of objects we have to dereference/clean.
            values = self._lookup_data()
            return _for_each_deep(
                values,
                lambda v: func(v, keys, attrs),
                levels=len(self.field.path_elements),
            )
        except KeyError:  # pragma: no cover
            return None


class ArbitraryPathRelation(ListRelation):
    """Relation type that resolves via an arbitrary path in the record.

    self.path_elements contain the segments of the path that are within lists.
    For example:
    - For paths like "a.b.c", path = [], relation_field="a.b.c"
    - For paths like "a.b.0.c", path = ["a.b"], relation_field="c"
    - For paths like "a.0.b.1.c", path = ["a", "b"], relation_field="c"
    - For paths like "a.1", path = ["a"], relation_field=None

    If path_elements is empty, the relation resolves to a single object (no array
    levels at all). Otherwise, ids and values are stored as lists that can contain
    other lists arbitrarily nested. The total depth of nesting is given by the
    length of self.path_elements + 1 if self.relation_field is not None
    or length of self.path_elements if self.relation_field is None.
    """

    result_cls = ArbitraryPathResult

    def __init__(
        self,
        *args: Any,
        array_paths: list[str] | None = None,
        relation_field: str | None = None,
        **kwargs: Any,
    ):
        """Initialize the relation."""
        # None and [] both mean "no array levels" - normalize to [] so that
        # self.path_elements is always a plain list, never None.
        self.path_elements: list[str] = array_paths if array_paths is not None else []
        super().__init__(*args, relation_field=relation_field, **kwargs)

    @override
    def exists_many(self, ids: Any) -> bool:  # type: ignore[override]
        """Return True if all ids exists."""
        if not self.path_elements:
            # no array levels: ids is a single, already-parsed id
            return bool(self.exists(ids))

        # ids is a list that might recursively contain lists that contain ids
        def flatten(nested_list: Any) -> Generator[Any]:
            for item in nested_list:
                if isinstance(item, (list, tuple)):
                    yield from flatten(item)
                else:
                    yield item

        return all(self.exists(i) for i in flatten(ids))

    @override
    def parse_value(self, value: Any) -> Any:  # type: ignore[override]
        """Parse a record (or ID) to the ID to be stored.

        Returns a single id (no array levels) or a, possibly nested, list of ids.
        """
        if not self.path_elements:
            # no array levels: value is the raw id (or record) directly, not a
            # list item wrapped via relation_field
            return super(ListRelation, self).parse_value(value)
        return _for_each_deep(value, self._parse_single_value, levels=len(self.path_elements))

    def _parse_single_value(self, value: Any) -> Any:
        """Parse a single value using the parent class method.

        Note: we are skipping the list's parse_value here and calling
        the next one after ListRelation in mro chain. That might be, for example,
        PIDRelation.parse_value
        """
        if self.relation_field:
            try:
                return super(ListRelation, self).parse_value(dict_lookup(value, self.relation_field))
            except KeyError:  # pragma: no cover
                return None
        else:
            return super(ListRelation, self).parse_value(value)

    @override
    def set_value(
        self,
        record: Record,
        value: list[Any] | tuple[Any],
    ) -> None:  # type: ignore[override]
        """Set the relation value."""
        store_values = self.parse_value(value)

        if not self.exists_many(store_values):
            raise InvalidRelationValue(f'One of the values "{store_values}" is invalid.')

        total_depth = len(self.path_elements)

        for path_indices, path_value in _deep_enumerate(store_values, total_depth):
            r: Any = record
            self._set_value_at_path(r, path_indices, {self._value_key_suffix: path_value})

    def _set_value_at_path(self, r: Any, path_indices: list[int], path_value: Any) -> None:
        """Set the value at the given path indices."""
        pe = [
            *self.path_elements,
        ]
        if self.relation_field:
            pe.append(self.relation_field)

        # pe might be 1 longer than path_indices, that's why we use zip_longest
        zipped = list(zip_longest(pe, path_indices, fillvalue=None))
        for idx, (subpath, index) in enumerate(zipped[:-1]):
            if not subpath:
                raise InvalidRelationValue(  # pragma: no cover
                    f"Invalid structure, missing key at index {idx} in [{self.path_elements}, {path_indices}]."
                )
            if index is None:
                raise InvalidRelationValue(  # pragma: no cover
                    f"Invalid structure, missing index at {subpath} in [{self.path_elements}, {path_indices}]."
                )
            r = self._set_default_value_at_path(r, subpath, index, path_indices)

        last_path, last_index = zipped[-1]
        if last_path is None:  # pragma: no cover
            raise InvalidRelationValue("Implementation error.")
        if last_index is None:
            # we have a relation_field at the end, so set it directly
            dict_set(r, last_path, path_value)
        else:
            # no relation_field at the end, so we set the whole object at the index
            try:
                val = dict_lookup(r, last_path)
            except KeyError:
                val = []
                dict_set(r, last_path, val)
            if last_index < len(val):
                val[last_index] = path_value
            elif last_index == len(val):
                val.append(path_value)
            else:
                raise InvalidRelationValue(  # pragma: no cover # just sanity check
                    f"Invalid structure, missing index {last_index} "
                    f"at {last_path} in [{self.path_elements}, {path_indices}]."
                )

    def _set_default_value_at_path(self, r: Any, subpath: str, index: int, path_indices: list[int]) -> Any:
        """Set default value of [] at the given path if missing."""
        # look up the subpath and create it if missing
        try:
            val = dict_lookup(r, subpath)
        except KeyError:
            dict_set(r, subpath, [])
            val = dict_lookup(r, subpath)
        if not isinstance(val, list):
            raise InvalidRelationValue(  # pragma: no cover
                f"Invalid structure, expecting list at {subpath} in [{self.path_elements}, {path_indices}]."
            )

        # now we have the array - if the index is within array, return the value at the index
        if index < len(val):
            return val[index]

        # if the index is exactly at the end of the array, we can append a new default value,
        # which is always an empty dict
        if index == len(val):
            # append new default value which is always empty dict
            r = {}
            val.append(r)
            return r

        # we can not skip indices, so if that would happen, raise error
        raise InvalidRelationValue(  # pragma: no cover
            f"Invalid structure, missing index {index} at {subpath} in [{self.path_elements}, {path_indices}]."
        )


def _deep_enumerate(nested_list: Any, max_depth: int, depth: int = 0) -> Generator[tuple[list[int], Any]]:
    """Enumerate all non-list items in a nested list structure."""
    if max_depth == 0:
        yield [], nested_list
        return
    for index, item in enumerate(nested_list):
        current_path = [index]
        if depth < max_depth - 1 and isinstance(item, (list, tuple)):
            for sub_path, sub_item in _deep_enumerate(item, max_depth, depth + 1):
                yield current_path + sub_path, sub_item
        else:
            yield current_path, item


def _for_each_deep(nested_list: Any, func: Any, levels: int) -> Any:
    """Apply a function to each non-list item in a nested list structure.

    Returns func(nested_list) directly when levels is 0 (no list to iterate over),
    otherwise a, possibly nested, list of func's results.
    """
    if levels == 0:
        return func(nested_list)
    result = []
    for item in nested_list:
        if isinstance(item, (list, tuple)) and levels > 1:
            result.append(_for_each_deep(item, func, levels=levels - 1))
        else:
            result.append(func(item))
    return result


class PIDArbitraryPathRelation(ArbitraryPathRelation, PIDRelation):  # type: ignore[override, misc]
    """PID relation type that resolves via an arbitrary path in the record."""


class InternalRelations(SystemField):
    """System field for managing internal relations.

    Returns a cached InternalRelationsLookup instance.
    """

    @override
    def __get__(  # type: ignore[override]
        self, record: Record | None, owner: type | None = None
    ) -> InternalRelations | InternalRelationsLookup:
        """Return the cached lookup table for the record."""
        if record is None:
            return self
        # Check cache first
        cached = self._get_cache(record)
        if cached is not None:
            return cached
        # Build and cache the lookup table
        lookup = InternalRelationsLookup(record)
        self._set_cache(record, lookup)
        return lookup


class InternalRecord(dict):
    """Internal record type that holds the lookup table for internal relations."""

    def __init__(self, data: dict[str, Any], id_: str, revision_id: int | None):
        """Initialize the internal record with the given data and IDs."""
        super().__init__(data)
        self.id = id_
        self.revision_id = revision_id


class InternalRelationsLookup:
    """Lookup table for internal relations, built from target paths."""

    def __init__(self, record: Record):
        """Initialize the lookup table from record parts identified by `id` fields."""
        self.record = record

    def _lookup_paths(self, data: Any, path: list[str]) -> Iterator[tuple[str, dict[str, Any]]]:
        """Lookup all dictionaries that have an `id` field.

        Return a generator of (path, value) pairs,
        where the path is the dot-separated key path to the value (excluding array indices).
        """
        if isinstance(data, (list, tuple)):
            for d in data:
                yield from self._lookup_paths(d, path)
        elif isinstance(data, dict):
            for key, value in data.items():
                yield from self._lookup_paths(value, [*path, key])
            if "id" in data:
                yield (".".join(path), data)

    @cached_property
    def lookup_table(self) -> dict[str, dict[str, Any]]:
        """Return the lookup table."""
        lookup_table: dict[str, dict[str, Any]] = {}
        for pth, value in self._lookup_paths(self.record, []):
            value_id = value["id"]
            path_rec = lookup_table.setdefault(pth, {})
            if value_id in path_rec:
                raise ValidationError(f"Duplicate id '{value_id}' found in path '{pth}'", field_name=pth)
            path_rec[value_id] = InternalRecord(value, value_id, self.record.revision_id)
        return lookup_table

    def __contains__(self, id_: tuple[str, str]) -> bool:
        """Check if the id is in the lookup table."""
        return id_[0] in self.lookup_table and id_[1] in self.lookup_table[id_[0]]

    def __getitem__(self, id_: tuple[str, str]) -> Any:
        """Get the value for the id from the lookup table."""
        return self.lookup_table[id_[0]][id_[1]]


class InternalRelationResult(ArbitraryPathResult):
    """Result of an internal relation."""

    def resolve(self, id_: str) -> Record | None:
        """Resolve the relation by looking up the id in the internal relations lookup table."""
        internal_relations: InternalRelationsLookup = self.record.internal_relations
        for pth in self.target_paths:
            if (pth, id_) in internal_relations:
                return internal_relations[(pth, id_)]
        return None

    def exists(self, id_: str) -> bool:
        """Check existence via this result's own resolve (which has record context).

        RelationBase.exists() would call the field's resolve() instead (it has no
        record context and is a deliberate NotImplementedError stub), since exists()
        is never defined on any Result class and so is proxied to the field via
        RelationResult.__getattr__.
        """
        return self.resolve(id_) is not None


class InternalRelation(ArbitraryPathRelation):
    """A relation that resolves to a part of the same record.

    Note: there needs to be an internal_relations field on the record class
    for this relation to work and our target_paths must match a target path
    in the internal_relations field.

    ```
        internal_relations = InternalRelations(target_paths=["...", "..."])
    ```
    """

    result_cls = InternalRelationResult

    def __init__(self, *args: Any, target_paths: list[str], **kwargs: Any):
        """Initialize the relation with the target paths."""
        self.target_paths = target_paths
        super().__init__(*args, **kwargs)

    def resolve(self, id_: str) -> Record | None:
        """Raise - resolution needs record context, only available on InternalRelationResult.resolve."""
        raise NotImplementedError("This method should never be called, use InternalRelationResult.resolve instead.")

    def set_value(self, record: Record, value: list[Any] | tuple[Any]) -> None:
        """Raise - setting internal relation values is not supported."""
        raise NotImplementedError("InternalRelation.set_value is not supported for internal relations.")


# Deprecated aliases kept for backward compatibility - prefer the ArbitraryPath* names above.
ArbitraryNestedListResult = ArbitraryPathResult
ArbitraryNestedListRelation = ArbitraryPathRelation
PIDArbitraryNestedListRelation = PIDArbitraryPathRelation
