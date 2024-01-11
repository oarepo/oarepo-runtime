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
    if output_file == "-":
        print(
            json.dumps(
                configuration, indent=4, ensure_ascii=False, default=lambda x: str(x)
            )
        )
    else:
        with open(output_file, "w") as f:
            json.dump(configuration, f, ensure_ascii=False, default=lambda x: str(x))
