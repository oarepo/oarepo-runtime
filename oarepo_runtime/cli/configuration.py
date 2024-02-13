import json

import click
from flask import current_app
from flask.cli import with_appcontext
from werkzeug.local import LocalProxy

from .base import oarepo


@oarepo.command(name="configuration")
@click.argument("output_file", default="-")
@with_appcontext
def configuration_command(output_file):
    configuration = {
        k: v for k, v in current_app.config.items() if not isinstance(v, LocalProxy)
    }

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
                configuration, indent=4, ensure_ascii=False, default=lambda x: str(x)
            )
        )
    else:
        with open(output_file, "w") as f:
            json.dump(configuration, f, ensure_ascii=False, default=lambda x: str(x))
