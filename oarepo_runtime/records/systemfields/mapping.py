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

    @classmethod
    def search_dump(cls, data, record):
        """Dump custom field."""

    @classmethod
    def search_load(cls, data, record_cls):
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
