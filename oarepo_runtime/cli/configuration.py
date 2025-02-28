import json

import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.local import LocalProxy

from .base import oarepo

def create_config_dict(config):
    """Recursively create configuration dict without LocalProxies inside."""
    result = {}
    for k, v in config.items():
        if isinstance(v, dict):
            result[k] = create_config_dict(v)
        elif not isinstance(v, LocalProxy):
            result[k] = v
    return result

@oarepo.command(name="configuration")
@click.argument("output_file", default="-")
@with_appcontext
def configuration_command(output_file):
    configuration = create_config_dict(current_app.config)

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
            json.dump(configuration, f, skipkeys=True, ensure_ascii=False, default=lambda x: str(x))
