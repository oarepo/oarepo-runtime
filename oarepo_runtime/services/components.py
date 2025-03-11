from __future__ import annotations

import inspect
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Type

from flask import current_app
from invenio_accounts.models import User
from invenio_base.utils import obj_or_import_string
from invenio_drafts_resources.services.records.config import (
    RecordServiceConfig as DraftsRecordServiceConfig,
)
from invenio_rdm_records.services.config import RDMRecordServiceConfig
from invenio_records import Record
from invenio_records_resources.services import FileServiceConfig
from invenio_records_resources.services.records.config import (
    RecordServiceConfig as RecordsRecordServiceConfig,
)

from oarepo_runtime.proxies import current_oarepo
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

    for excluded_component in current_oarepo.rdm_excluded_components:
        if excluded_component in processed_components:
            processed_components.remove(excluded_component)

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
    
    The components must be classes of ServiceComponent.
    """

    affects: list[ComponentPlacement] = field(default_factory=list)
    """List of components that depend on this one."""

    star_depends: bool = False
    """True if this component depends on all other components."""

    star_affects: bool = False
    """True if this component affects all other components."""

    def __hash__(self) -> int:
        return id(self.component)

    def __eq__(self, other: Any) -> bool:
        return self.component is other.component

    def __repr__(self) -> str:
        depends_on = [d.component.__name__ for d in self.depends_on]
        affects = [a.component.__name__ for a in self.affects]
        if self.star_affects:
            affects.append("*")
        if self.star_depends:
            depends_on.append("*")
        r = [f"<{self.component.__name__}"]
        if depends_on:
            r.append(f" depends_on: {depends_on}")
        if affects:
            r.append(f" affects: {affects}")
        r.append(">")
        return "".join(r)

    def __str__(self) -> str:
        return repr(self)


def _sort_components(components) -> list[Type[ServiceComponent]]:
    """Sort components based on their dependencies while trying to
    keep the initial order as far as possible.

    Sorting algorithm:

    1. Select all "affects" components that has "*" in their "affects" list.
    2. Merge these components preserving other other "affects" and "depends_on" settings
       and output these

    3. put "depends_on: *" components aside for the moment
    4. Sort the remaining components by their dependencies

    5. process depends_on: * in a similar way as in 2.
    """

    placements: list[ComponentPlacement] = _prepare_component_placement(components)

    # placements that must be first as they affect all other components
    affects_placements = [p for p in placements if p.star_affects]

    # placements that must be last as they depend on all other components
    depends_on_placements = [p for p in placements if p.star_depends]

    # if a component affects another that affects all components,
    # add it to affects_placements
    #
    # A[affects *] B[affects A] C => adds B to affects_placements
    modified = True
    while modified:
        modified = False
        for p in placements:
            if (
                any(q in affects_placements for q in p.affects)
                and p not in affects_placements
            ):
                affects_placements.append(p)
                modified = True

    # if a component depends on another that depends on all components,
    # add it to depends_on_placements
    # A[depends_on *] B[depends_on A] C => adds B to depends_on_placements
    modified = True
    while modified:
        modified = False
        for p in placements:
            if (
                any(q in depends_on_placements for q in p.depends_on)
                and p not in depends_on_placements
            ):
                depends_on_placements.append(p)
                modified = True

    # those that do not affect or depend on all components
    middle_placements = [
        p
        for p in placements
        if p not in depends_on_placements and p not in affects_placements
    ]

    # sort placements inside each group by their respective depends on and affects
    # relationships, ignoring the star relationships
    ret = []
    ret.extend(_sort_placements(affects_placements))
    ret.extend(_sort_placements(middle_placements))
    ret.extend(_sort_placements(depends_on_placements))
    return ret


def _sort_placements(placements):
    """Sort placements based on their dependencies.

    The algorithm tries to keep the initial order as far as possible,
    while still respecting the dependencies.

    At first, for each component that affects another component, the algorithm
    moves the affecting component before the affected one one step at a time.

    When no more such moves are possible, the algorithm moves to the next step
    and does similar thing for components that depend on another component.

    The algorithm is repeated until all components are sorted. If they can not
    be after a set number of iterations, the algorithm raises an exception.
    """

    _filter_depends_on_and_affects(placements)

    for _ in range(10):
        for __ in range(10):
            # move components that affect other components before them
            modified = _move_affecting_components(placements)

            # move components that depend on other components after them
            if _move_depends_on_components(placements):
                modified = True

            # if the order was not modified, we are done
            if not modified:
                return (p.component for p in placements)
        else:
            # could not sort the components by simple move. This means that we are
            # in a situation where A C B[affects A depends on C] - we will try to
            # swap A with C and try again.
            _swap_out_of_order_components(placements)

    raise ValueError(f"Can not order components: {placements}")


def _swap_out_of_order_components(placements):
    for idx, placement in enumerate(placements):

        # we are looking for a situation: A C placement[affects A depends on C]
        # so if there are not depends on and affects, try the next one
        if not placement.depends_on or not placement.affects:
            continue

        depends_on = [(p, placements.index(p)) for p in placement.depends_on]
        affects = [(p, placements.index(p)) for p in placement.affects]

        # if there are no indices to swap, continue
        if not depends_on or not affects:
            continue

        # keep the indices in order
        depends_on.sort(key=lambda x: x[1])
        affects.sort(key=lambda x: x[1])

        depends_on_indices = [d[1] for d in depends_on]
        affects_indices = [a[1] for a in affects]

        swapped_depends_on = [d[0] for d in depends_on]
        swapped_affects = [a[0] for a in affects]

        # if the index of the component the current placement depends on
        # is lower that any of the components that depend on the current placement,
        # we are ok as the placement can be moved to the space between them,
        # so just continue
        if max(depends_on_indices) < min(affects_indices):
            continue

        # add all to an array and sort them. This way depends on will be after
        # affects, keeping the positions inside the group
        indices = sorted([*affects_indices, *depends_on_indices])

        for idx, dep in zip(
            indices,
            [*swapped_depends_on, *swapped_affects],
        ):
            placements[idx] = dep


def _filter_depends_on_and_affects(placements):
    """Filter out dependencies on components that are not in the placements list."""
    for placement in placements:
        placement.depends_on = [p for p in placement.depends_on if p in placements]
        placement.affects = [p for p in placement.affects if p in placements]


def _move_affecting_components(placements):
    modified = False

    for idx, placement in list(enumerate(placements)):
        if not placement.affects:
            continue
        min_index = min(placements.index(a) for a in placement.affects)
        if min_index < idx:
            placements.remove(placement)
            placements.insert(min_index, placement)
            modified = True
    return modified


def _move_depends_on_components(placements):
    modified = False
    for idx, placement in reversed(list(enumerate(placements))):
        if not placement.depends_on:
            continue
        max_index = max(placements.index(a) for a in placement.depends_on)
        if max_index > idx:
            placements.remove(placement)
            placements.insert(max_index, placement)
            modified = True
    return modified


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
        placement.star_depends = "*" in getattr(placement.component, "depends_on", [])
        placement.star_affects = "*" in getattr(placement.component, "affects", [])

        for dep in getattr(placement.component, "depends_on", []):
            if dep == "*":
                continue
            dep = obj_or_import_string(dep)
            for pl in _matching_placements(placements_without_this, dep):
                if pl not in placement.depends_on:
                    placement.depends_on.append(pl)

        for dep in getattr(placement.component, "affects", []):
            if dep == "*":
                continue
            dep = obj_or_import_string(dep)
            for pl in _matching_placements(placements_without_this, dep):
                if pl not in placement.affects:
                    placement.affects.append(pl)

    return placements
