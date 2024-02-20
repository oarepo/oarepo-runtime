from invenio_records.systemfields import SystemField

from .mapping import MappingSystemFieldMixin


class RecordStatusResult:
    def __init__(self, record, attr_name):
        self.record = record
        self.attr_name = attr_name


class RecordStatusSystemField(MappingSystemFieldMixin, SystemField):
    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "keyword",
            },
        }

    def search_load(self, data, record_cls):
        data.pop(self.attr_name, None)

    def search_dump(self, data, record):
        if getattr(record, "is_draft"):
            data[self.attr_name] = "draft"
        else:
            data[self.attr_name] = "published"

    def __get__(self, record, owner=None):
        """Accessing the attribute."""
        # Class access
        if record is None:
            return self
        return RecordStatusResult(record, self.attr_name)
