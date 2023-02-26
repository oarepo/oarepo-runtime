import importlib_metadata
from invenio_records_resources.resources import RecordResourceConfig


class Records2ResourceConfig(RecordResourceConfig):
    """Records2Record resource config."""

    blueprint_name = "Records2"
    url_prefix = "/records2/"

    @property
    def response_handlers(self):
        entrypoint_response_handlers = {}
        for x in importlib_metadata.entry_points(
            group="invenio.records2.response_handlers"
        ):
            entrypoint_response_handlers.update(x.load())
        return {**super().response_handlers, **entrypoint_response_handlers}
