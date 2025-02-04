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
    component_id: int = field(init=False)
    component: ServiceComponent
    depends_on: list[ComponentPlacement] = field(default_factory=list)
    affects: list[ComponentPlacement] = field(default_factory=list)
    tension_up: int = 0
    tension_down: int = 0

    def __post_init__(self):
        self.component_id = id(self.component)

    def __hash__(self) -> int:
        return self.component_id

    def __eq__(self, other: ComponentPlacement) -> bool:
        return self.component_id == other.component_id


def _sort_components(components):
    placements: list[ComponentPlacement] = _prepare_component_placement(components)
    by_position = {p: idx for idx, p in enumerate(placements)}

    for i in range(100):
        tension = _compute_tensions(placements, by_position)
        if not tension:
            break
        swap_happened = _apply_tensions(placements, by_position)
        # todo: break on swap happened or on tension ?
    else:
        raise Exception("Failed to resolve component dependencies")

    return [p.component for p in placements]


def _prepare_component_placement(components):
    placements = []
    by_id = {}
    for idx, c in enumerate(components):
        placement = ComponentPlacement(component=c)
        placements.append(placement)
        by_id[id(c)] = placement

    for placement in placements:
        for dep in getattr(placement.component, "depends_on", []):
            if dep == "*":
                for pl in placements:
                    if pl != placement:
                        placement.depends_on.append(pl)
                        pl.affects.append(placement)
            else:
                for pl in placements:
                    if pl != placement and isinstance(pl.component, dep):
                        placement.depends_on.append(pl)
                        pl.affects.append(placement)

        for dep in getattr(placement.component, "affects", []):
            if dep == "*":
                for pl in placements:
                    if pl != placement:
                        placement.affects.append(pl)
                        pl.depends_on.append(placement)
            else:
                for pl in placements:
                    if pl != placement and isinstance(pl.component, dep):
                        placement.affects.append(pl)
                        pl.depends_on.append(placement)

    return placements


def _compute_tensions(
    placements: list[ComponentPlacement], by_position: dict[ComponentPlacement, int]
):
    tensions = 0
    for placement_position, placement in enumerate(placements):
        placement.tension_down = 0
        placement.tension_up = 0

        for dep in placement.depends_on:
            dep_position = by_position[dep]

            if placement_position < dep_position:
                placement.tension_up += dep_position - placement_position
                tensions += 1
        for dep in placement.affects:
            dep_position = by_position[dep]
            if placement_position > dep_position:
                placement.tension_down += placement_position - dep_position
                tensions += 1
    return tensions


def _apply_tensions(
    placements: list[ComponentPlacement], by_position: dict[ComponentPlacement, int]
) -> bool:
    swap_happened = False
    # one round of bubble sort up and down
    for idx in range(len(placements) - 1):
        placement = placements[idx]

        if placement.tension_up <= 0:
            continue

        next_placement = placements[idx + 1]
        if next_placement.tension_up < placement.tension_up:
            placements[idx], placements[idx + 1] = next_placement, placement
            by_position[placement] = idx + 1
            by_position[next_placement] = idx
            placement.tension_up -= 1
            swap_happened = True

    for idx in range(len(placements) - 1, 0, -1):
        placement = placements[idx]
        if placement.tension_down <= 0:
            continue

        prev_placement = placements[idx - 1]
        if prev_placement.tension_down < placement.tension_down:
            placements[idx - 1], placements[idx] = placement, prev_placement
            by_position[placement] = idx - 1
            by_position[prev_placement] = idx
            placement.tension_down -= 1
            swap_happened = True

    return swap_happened
