from invenio_pidstore.errors import PIDUnregistered
from oarepo import __version__ as oarepo_version

# compatibility setting between invenio rdm 11 and invenio rdm 12
# can be removed when invenio rdm 11 is no longer supported
if oarepo_version.split(".")[0] == "11":
    from invenio_records_resources.references.resolvers.records import RecordProxy as InvenioRecordProxy
else:
    from invenio_records_resources.references.entity_resolvers.records import (
        RecordProxy as InvenioRecordProxy,
    )

from sqlalchemy.exc import NoResultFound


def set_field(result, resolved_dict, field_name):
    from_metadata = resolved_dict.get("metadata", {}).get(field_name)
    from_data = resolved_dict.get(field_name)

    if from_metadata:
        result.setdefault("metadata", {})[field_name] = from_metadata
    if from_data:
        result[field_name] = from_data


class RecordProxy(InvenioRecordProxy):
    picked_fields = ["title", "creators", "contributors"]

    def pick_resolved_fields(self, identity, resolved_dict):
        """Select which fields to return when resolving the reference."""
        resolved_fields = super().pick_resolved_fields(identity, resolved_dict)

        for fld in self.picked_fields:
            set_field(resolved_fields, resolved_dict, fld)

        return resolved_fields


class DraftProxy(RecordProxy):
    def _resolve(self):
        pid_value = self._parse_ref_dict_id()
        try:
            return self.record_cls.pid.resolve(pid_value, registered_only=False)
        except (PIDUnregistered, NoResultFound):
            # try checking if it is a published record before failing
            return self.record_cls.pid.resolve(pid_value)
