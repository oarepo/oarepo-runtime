# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Communities is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Communities system field."""
import functools
import inspect

from invenio_records.systemfields import SystemField

from oarepo_runtime.records.owners import OwnerEntityResolverRegistry
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin


class OwnerRelationManager(set):

    def __init__(self, record_id, serialized_owners):
        self._serialized_owners = serialized_owners
        self._owners_initialized = False
        self._resolve()
        for name, function in inspect.getmembers(set, predicate=callable):
            self._create_wrapper(name, function)

    def _create_wrapper(self, name, function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            self._resolve()
            return function(self, *args, **kwargs)

        try:
            setattr(self, name, wrapper)
        except TypeError as e:
            pass

    # from oarepo_requests utils, dependancy on that would be wrong here, right?
    # invenio_requests is ok<

    #
    # API
    #

    def to_dict(self):
        if self._serialized_owners is not None:
            return self._serialized_owners
        return [OwnerEntityResolverRegistry.reference_entity(x) for x in self]

    def _resolve(self):
        if not self._owners_initialized:
            self._owners_initialized = True
            for ref in self._serialized_owners or []:
                self.add(OwnerEntityResolverRegistry.resolve_reference(ref))
            self._serialized_owners = None


"""
class OwnerRelationManager(set):


    def __init__(self, record_id, serialized_owners):
        for name, function in inspect.getmembers(set, predicate=callable):
            self._create_wrapper(name, function)
        self._owners_initialized = False
        self._serialized_owners = serialized_owners

    def _create_wrapper(self, name, function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            self._resolve()
            return function(self, *args, **kwargs)
        try:
            setattr(self, name, wrapper)
        except TypeError as e:
            pass

    # from oarepo_requests utils, dependancy on that would be wrong here, right?
    # invenio_requests is ok<

    #
    # API
    #

    def to_dict(self):
        if self._serialized_owners is not None:
            return self._serialized_owners
        serialized_owners = [OwnerEntityResolverRegistry.reference_entity(x) for x in self]
        return serialized_owners

    def _resolve(self):
        if not self._owners_initialized:
            self._owners_initialized = True
            for element in self._serialized_owners or []:
                self.add(OwnerEntityResolverRegistry.resolve_reference(element))
            self._serialized_owners = None
"""


class OwnersField(MappingSystemFieldMixin, SystemField):
    """Communites system field for managing relations to communities."""

    def __init__(self, key="owners", manager_cls=None):
        """Constructor."""
        self._manager_cls = manager_cls or OwnerRelationManager
        super().__init__(key=key)

    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "object",
            },
        }

    def pre_commit(self, record):
        """Commit the communities field."""
        manager = self.obj(record)
        self.set_dictkey(record, manager.to_dict())

    def pre_dump(self, record, data, dumper=None):
        """Called before a record is dumped."""
        # parent record commit op is not called during update, resulting in the parent not being converted correctly into 'dict', ie. the dict() function in invenio_records.dumpers.base #36 works incorrectly
        manager = self.obj(record)
        self.set_dictkey(record, manager.to_dict())

    def obj(self, record):
        """Get or crate the communities manager."""
        # Check cache
        obj = self._get_cache(record)
        if obj is not None:
            return obj

        serialized_owners = self.get_dictkey(record)
        # Create manager
        obj = self._manager_cls(record.id, serialized_owners)
        self._set_cache(record, obj)
        return obj

    def __get__(self, record, owner=None):
        """Get the persistent identifier."""
        if record is None:
            return self
        return self.obj(record)
