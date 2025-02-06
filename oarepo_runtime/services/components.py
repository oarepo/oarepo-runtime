from __future__ import annotations

import inspect
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Type

from flask import current_app
from invenio_accounts.models import User
from invenio_drafts_resources.services.records.config import (
    RecordServiceConfig as DraftsRecordServiceConfig,
)
from invenio_rdm_records.services.config import RDMRecordServiceConfig
from invenio_records import Record
from invenio_records_resources.services import FileServiceConfig
from invenio_records_resources.services.records.config import (
    RecordServiceConfig as RecordsRecordServiceConfig,
)

from oarepo_runtime.services.custom_fields import (
    CustomFields,
    CustomFieldsMixin,
    InlinedCustomFields,
)
from oarepo_runtime.services.generators import RecordOwners

try:
    from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
except ImportError:
    from invenio_records_resources.services.uow import (
        RecordCommitOp as ParentRecordCommitOp,
    )

from invenio_records_resources.services.records.components import ServiceComponent


class OwnersComponent(ServiceComponent):
    def create(self, identity, *, record, **kwargs):
        """Create handler."""
        self.add_owner(identity, record)

    def add_owner(self, identity, record, commit=False):
        if not hasattr(identity, "id") or not isinstance(identity.id, int):
            return

        owners = getattr(record.parent, "owners", None)
        if owners is not None:
            user = User.query.filter_by(id=identity.id).first()
            record.parent.owners.add(user)
            if commit:
                self.uow.register(ParentRecordCommitOp(record.parent))

    def update(self, identity, *, record, **kwargs):
        """Update handler."""
        self.add_owner(identity, record, commit=True)

    def update_draft(self, identity, *, record, **kwargs):
        """Update handler."""
        self.add_owner(identity, record, commit=True)

    def search_drafts(self, identity, search, params, **kwargs):
        new_term = RecordOwners().query_filter(identity)
        if new_term:
            return search.filter(new_term)
        return search


from datetime import datetime


class DateIssuedComponent(ServiceComponent):
    def publish(self, identity, data=None, record=None, errors=None, **kwargs):
        """Create a new record."""
        if "dateIssued" not in record["metadata"]:
            record["metadata"]["dateIssued"] = datetime.today().strftime("%Y-%m-%d")


class CFRegistry:
    def __init__(self):
        self.custom_field_names = defaultdict(list)

    def lookup(self, record_type: Type[Record]):
        if record_type not in self.custom_field_names:
            for fld in inspect.getmembers(
                record_type, lambda x: isinstance(x, CustomFieldsMixin)
            ):
                self.custom_field_names[record_type].append(fld[1])
        return self.custom_field_names[record_type]


cf_registry = CFRegistry()


class CustomFieldsComponent(ServiceComponent):
    def create(self, identity, data=None, record=None, **kwargs):
        """Create a new record."""
        self._set_cf_to_record(record, data)

    def update(self, identity, data=None, record=None, **kwargs):
        """Update a record."""
        self._set_cf_to_record(record, data)

    def _set_cf_to_record(self, record, data):
        for cf in cf_registry.lookup(type(record)):
            if isinstance(cf, CustomFields):
                setattr(record, cf.attr_name, data.get(cf.key, {}))
            elif isinstance(cf, InlinedCustomFields):
                config = current_app.config.get(cf.config_key, {})
                for c in config:
                    record[c.name] = data.get(c.name)


def process_service_configs(service_config, *additional_components):
    processed_components = []
    target_classes = {
        RDMRecordServiceConfig,
        DraftsRecordServiceConfig,
        RecordsRecordServiceConfig,
        FileServiceConfig,
    }

    for end_index, cls in enumerate(type(service_config).mro()):
        if cls in target_classes:
            break

    # We need this because if the "build" function is present in service_config,
    # there are two service_config instances in the MRO (Method Resolution Order) output.
    start_index = 2 if hasattr(service_config, "build") else 1

    service_configs = type(service_config).mro()[start_index : end_index + 1]
    for config in service_configs:
        if hasattr(config, "build"):
            config = config.build(current_app)

        if hasattr(config, "components"):
            component_property = config.components
            if isinstance(component_property, list):
                processed_components.extend(component_property)
            elif isinstance(component_property, tuple):
                processed_components.extend(list(component_property))
            else:
                raise ValueError(f"{config} component's definition is not supported")

    processed_components.extend(additional_components)
    processed_components = _sort_components(processed_components)
    return processed_components


@dataclass
class ComponentPlacement:
    """Component placement in the list of components.

    This is a helper class used in the component ordering algorithm.
    """

    component: Type[ServiceComponent]
    """Component to be ordered."""

    depends_on: list[ComponentPlacement] = field(default_factory=list)
    """List of components this one depends on.
    
    The components must be classes of ServiceComponent or '*' to denote
    that this component depends on all other components and should be placed last.
    """

    affects: list[ComponentPlacement] = field(default_factory=list)
    """List of components that depend on this one.
    
    This is a temporary list used for evaluation of '*' dependencies
    but does not take part in the sorting algorithm."""

    def __hash__(self) -> int:
        return id(self.component)

    def __eq__(self, other: ComponentPlacement) -> bool:
        return self.component is other.component


def _sort_components(components):
    """Sort components based on their dependencies while trying to
    keep the initial order as far as possible."""

    placements: list[ComponentPlacement] = _prepare_component_placement(components)
    placements = _propagate_dependencies(placements)

    ret = []
    while placements:
        without_dependencies = [p for p in placements if not p.depends_on]
        if not without_dependencies:
            raise ValueError("Circular dependency detected in components.")
        for p in without_dependencies:
            ret.append(p.component)
            placements.remove(p)
            for p2 in placements:
                if p in p2.depends_on:
                    p2.depends_on.remove(p)
    return ret


def _matching_placements(placements, dep_class_or_factory):
    for pl in placements:
        pl_component = pl.component
        if not inspect.isclass(pl_component):
            pl_component = type(pl_component(service=object()))
        if issubclass(pl_component, dep_class_or_factory):
            yield pl


def _prepare_component_placement(components) -> list[ComponentPlacement]:
    """Convert components to ComponentPlacement instances and resolve dependencies."""
    placements = []
    for idx, c in enumerate(components):
        placement = ComponentPlacement(component=c)
        placements.append(placement)

    # direct dependencies
    for idx, placement in enumerate(placements):
        placements_without_this = placements[:idx] + placements[idx + 1 :]
        for dep in getattr(placement.component, "depends_on", []):
            if dep == "*":
                continue
            for pl in _matching_placements(placements_without_this, dep):
                placement.depends_on.append(pl)
                pl.affects.append(placement)

        for dep in getattr(placement.component, "affects", []):
            if dep == "*":
                continue
            for pl in _matching_placements(placements_without_this, dep):
                placement.affects.append(pl)
                pl.depends_on.append(placement)

    # star dependencies
    for idx, placement in enumerate(placements):
        placements_without_this = placements[:idx] + placements[idx + 1 :]
        if "*" in getattr(placement.component, "depends_on", []):
            for pl in placements_without_this:
                # if this placement is not in placements that pl depends on
                # (added via direct dependencies above), add it
                if placement not in pl.depends_on:
                    placement.depends_on.append(pl)
                    pl.affects.append(placement)

        if "*" in getattr(placement.component, "affects", []):
            for pl in placements_without_this:
                # if this placement is not in placements that pl affects
                # (added via direct dependencies above), add it
                if placement not in pl.affects:
                    placement.affects.append(pl)
                    pl.depends_on.append(placement)
    return placements


def _propagate_dependencies(
    placements: list[ComponentPlacement],
) -> list[ComponentPlacement]:
    # now propagate dependencies
    dependency_propagated = True
    while dependency_propagated:
        dependency_propagated = False
        for placement in placements:
            for dep in placement.depends_on:
                for dep_of_dep in dep.depends_on:
                    if dep_of_dep not in placement.depends_on:
                        placement.depends_on.append(dep_of_dep)
                        dep_of_dep.affects.append(placement)
                        dependency_propagated = True

            for dep in placement.affects:
                for dep_of_dep in dep.affects:
                    if dep_of_dep not in placement.affects:
                        placement.affects.append(dep_of_dep)
                        dep_of_dep.depends_on.append(placement)
                        dependency_propagated = True

    return placements
