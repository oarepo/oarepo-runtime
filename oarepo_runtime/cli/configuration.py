import json
from collections.abc import Mapping, Sequence, Set

import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.local import LocalProxy

from .base import oarepo

def remove_lazy_objects(obj):
    if isinstance(obj, Sequence):
        if isinstance(obj, list):
            return [remove_lazy_objects(item) for item in obj if not isinstance(item, LocalProxy)]
        elif isinstance(obj, tuple):
            return tuple(remove_lazy_objects(item) for item in obj if not isinstance(item, LocalProxy))
        elif not isinstance(obj, LocalProxy):
            return obj # strings, bytes, bytesarray etc.
    elif isinstance(obj, Set):
        if isinstance(obj, frozenset):
            return frozenset(remove_lazy_objects(item) for item in obj if not isinstance(item, LocalProxy))
        return {remove_lazy_objects(item) for item in obj if not isinstance(item, LocalProxy)}
    elif isinstance(obj, Mapping):
        return {k: remove_lazy_objects(v) for k, v in obj.items() if not isinstance(v, LocalProxy)}
    elif not isinstance(obj, LocalProxy):
        return obj # everything else that is not localproxy

@oarepo.command(name="configuration")
@click.argument("output_file", default="-")
@with_appcontext
def configuration_command(output_file):
    configuration = remove_lazy_objects(current_app.config)

    try:
        invenio_db = current_app.extensions["invenio-db"]
        alembic_config = invenio_db.alembic.config
        configuration["ALEMBIC_LOCATIONS"] = alembic_config.get_main_option(
            "version_locations"
        ).split(",")
    except Exception as e:
        configuration["ALEMBIC_LOCATIONS_ERROR"] = str(e)

    if output_file == "-":
        print(
            json.dumps(
                configuration, skipkeys=True, indent=4, ensure_ascii=False, default=lambda x: str(x)
            )
        )
    else:
        with open(output_file, "w") as f:
            json.dump(configuration, f,skipkeys=True, ensure_ascii=False, default=lambda x: str(x))
