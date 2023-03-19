from flask import current_app
from werkzeug.utils import import_string

from oarepo_runtime.datastreams.errors import DataStreamCatalogueError

DATASTREAM_READERS = "DATASTREAMS_READERS"
DATASTREAMS_TRANSFORMERS = "DATASTREAMS_TRANSFORMERS"
DATASTREAMS_WRITERS = "DATASTREAMS_WRITERS"


def get_instance(config_section, clz, entry, **kwargs):
    entry = {**entry}
    if isinstance(clz, str):
        clz = entry.pop(clz)
        try:
            clz = (
                current_app.config[config_section].get(clz)
                or current_app.config[f"DEFAULT_{config_section}"][clz]
            )
        except KeyError:
            raise DataStreamCatalogueError(
                f"Do not have implementation - '{clz}' not defined in {config_section} config"
            )
        if isinstance(clz, str):
            clz = import_string(clz)
    try:
        return clz(**entry, **kwargs)
    except Exception as e:
        args = {**entry, **kwargs}
        raise DataStreamCatalogueError(
            f"Exception instantiating {clz} with arguments {args}"
        ) from e
