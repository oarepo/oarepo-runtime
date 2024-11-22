import inspect
from collections import defaultdict
from typing import Type

from flask import current_app
from invenio_accounts.models import User
from invenio_records import Record

from oarepo_runtime.services.custom_fields import CustomFieldsMixin, CustomFields, InlinedCustomFields
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
            for fld in inspect.getmembers(record_type, lambda x: isinstance(x, CustomFieldsMixin)):
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
                    record[c.name] =data.get(c.name)

def process_service_configs(service_configs):
    """
    Processes a list of service_config classes. If a class has a `components` attribute,
    it extends the result with the values in it.

    :param service_config: List of service_config classes to process.
    :return: A flattened list of processed components.
    """
    processed_components = []

    for config in service_configs:

        if hasattr(config, "build"):
            config = config.build(current_app)

        if hasattr(config, 'components'):
            component_property = config.components
            if isinstance(component_property, list):
                processed_components.extend(component_property)
            elif isinstance(component_property, tuple):
                processed_components.extend(list (component_property))
            else:
                raise ValueError(f"{config} component's definition is not supported")

    return processed_components