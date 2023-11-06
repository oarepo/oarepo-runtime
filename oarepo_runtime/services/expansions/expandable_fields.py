from invenio_records.dictutils import dict_lookup, dict_set
from invenio_records_resources.services.records.results import ExpandableField


class ReferencedRecordExpandableField(ExpandableField):
    def __init__(self, field_name, keys, service, pid_field="id"):
        super().__init__(field_name)
        self.keys = keys
        self.pid_field = pid_field
        self.service = service

    def get_value_service(self, value):
        if self.pid_field is None:
            return value, self.service
        return dict_lookup(value, self.pid_field), self.service

    def pick(self, identity, resolved_rec):
        ret = {}
        for key in self.keys:
            dict_set(ret, key, dict_lookup(resolved_rec, key))
        return ret
