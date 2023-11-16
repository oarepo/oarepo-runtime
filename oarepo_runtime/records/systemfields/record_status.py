from invenio_records.systemfields import SystemField

from .mapping import MappingSystemFieldMixin


class RecordStatusResult(MappingSystemFieldMixin):
    def __init__(self, record, attr_name):
        self.record = record
        self.attr_name = attr_name

    def search_dump(self, data):
        if getattr(self.record, "is_draft"):
            data[self.attr_name] = "draft"
        else:
            data[self.attr_name] = "published"


class RecordStatusSystemField(MappingSystemFieldMixin, SystemField):
    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "keyword",
            },
        }

    def search_load(self, data):
        data.pop(self.attr_name, None)

    def __get__(self, record, owner=None):
        """Accessing the attribute."""
        # Class access
        if record is None:
            return self
        return RecordStatusResult(record, self.attr_name)
