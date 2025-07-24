"""todo refactor - SystemFieldsExt: remove this class, using only SystemField‘s pre_load/post_dump """
import inspect

from invenio_records.dumpers import SearchDumperExt

class MappingSystemFieldMixin:
    @property
    def mapping(self):
        return {}

    @property
    def mapping_settings(self):
        return {}

    @property
    def dynamic_templates(self):
        return []

    def search_dump(self, data, record):
        """Dump custom field."""

    def search_load(self, data, record_cls):
        """Load custom field."""

class SystemFieldDumperExt(SearchDumperExt):
    def dump(self, record, data):
        """Dump custom fields."""
        for cf in inspect.getmembers(
            type(record), lambda x: isinstance(x, MappingSystemFieldMixin)
        ):
            cf[1].search_dump(data, record=record)

    def load(self, data, record_cls):
        """Load custom fields."""
        for cf in inspect.getmembers(
            record_cls, lambda x: isinstance(x, MappingSystemFieldMixin)
        ):
            cf[1].search_load(data, record_cls=record_cls)
