# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Communities is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Communities system field."""

from invenio_records.systemfields import SystemField

from oarepo_runtime.records.owners import OwnerEntityResolverRegistry
from oarepo_runtime.records.systemfields import MappingSystemFieldMixin


class OwnerRelationManager:
    def __init__(self, record_id, serialized_owners):
        self._serialized_owners = serialized_owners
        self._deserialized_owners = None

    # from oarepo_requests utils, dependancy on that would be wrong here, right?
    # invenio_requests is ok<

    #
    # API
    #

    def to_dict(self):
        if self._serialized_owners is None:
            deserialized_owners = []
            for deserialized_owner in self._deserialized_owners or []:
                serialized_owner = OwnerEntityResolverRegistry.reference_entity(
                    deserialized_owner
                )
                if serialized_owner is None:
                    raise ValueError(
                        f"failed serialize owner; owner - {deserialized_owner}"
                    )
                deserialized_owners.append(serialized_owner)
            self._serialized_owners = deserialized_owners
        return self._serialized_owners

    def _resolve(self):
        if self._deserialized_owners is None:
            self._deserialized_owners = set()
            for ref in self._serialized_owners or []:
                self._deserialized_owners.add(
                    OwnerEntityResolverRegistry.resolve_reference(ref)
                )
            self._serialized_owners = None

    def add(self, owner):
        if owner is None:
            return
        self._resolve()
        self._deserialized_owners.add(owner)

    def remove(self, owner):
        if owner is None:
            return
        self._resolve()
        self._deserialized_owners.remove(owner)

    def __iter__(self):
        self._resolve()
        return iter(self._deserialized_owners)


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
                "properties": {"user": {"type": "keyword", "ignore_above": 256}},
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
