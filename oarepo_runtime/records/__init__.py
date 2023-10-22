import inspect

from invenio_records.dumpers import SearchDumperExt


class MappingSystemFieldMixin:
    @property
    def mapping(self):
        return {}

    @property
    def mapping_settings(self):
        return {}


class SystemFieldDumperExt(SearchDumperExt):
    def dump(self, record, data):
        """Dump custom fields."""
        for cf in inspect.getmembers(
            record, lambda x: isinstance(x, MappingSystemFieldMixin)
        ):
            cf[1].search_dump(data)

    def load(self, data, record_cls):
        """Load custom fields."""
        for cf in inspect.getmembers(
            record_cls, lambda x: isinstance(x, MappingSystemFieldMixin)
        ):
            cf[1].search_load(data)
