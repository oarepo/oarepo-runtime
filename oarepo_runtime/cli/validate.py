import sys

import click
import yaml
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records import Record
from invenio_records_resources.proxies import current_service_registry

from .base import oarepo

try:
    import json5 as json
except ImportError:
    import json

import sys
from io import StringIO


class CheckOk(Exception):
    pass


def dump_data(d):
    io = StringIO()
    yaml.safe_dump(d, io, allow_unicode=True)
    return io.getvalue()


@oarepo.command(
    help="Validate a record. Takes one or two parameters - service name as "
    "the first one, file name or stdin with record data as the second"
)
@click.argument("service-name")
@click.argument("record-file", required=False)
@click.option("--verbose/--no-verbose", is_flag=True)
@with_appcontext
def validate(service_name, record_file, verbose):
    try:
        service = current_service_registry.get(service_name)
    except KeyError:
        click.secho(f"Service {service_name} not found. Existing services:")
        for existing in sorted(current_service_registry._services):
            click.secho(f"    - {existing}")
        sys.exit(1)

    config = service.config
    schema = config.schema

    if not record_file:
        file_content = sys.stdin.read().strip()
    else:
        with open(record_file) as f:
            file_content = f.read()

    if file_content.startswith("{"):
        data = json.loads(file_content)
    else:
        data = list(yaml.safe_load_all(StringIO(file_content)))

    if not isinstance(data, list):
        data = [data]
    for idx, d in enumerate(data):
        try:
            loaded = schema().load(d)
        except Exception as e:
            click.secho(
                f"Marshmallow validation of record idx {idx + 1} failed",
                fg="red",
            )
            click.secho(dump_data(d))
            click.secho(e)
            continue

        click.secho(
            f"Marshmallow validation of record idx {idx+1} has been successful",
            fg="green",
        )

        rec: Record = config.record_cls(loaded)

        # Run pre create extensions to check vocabularies
        try:
            with db.session.begin_nested():
                for e in rec._extensions:
                    e.pre_commit(rec)
                raise CheckOk()
        except CheckOk:
            click.secho(
                f"Pre-commit hook of record idx {idx+1} has been successful", fg="green"
            )
        except Exception as e:
            click.secho(
                f"Pre-commit validation of record idx {idx + 1} failed",
                fg="red",
            )
            click.secho(dump_data(d))
            click.secho(e)
            continue

        if verbose:
            yaml.safe_dump(loaded, sys.stdout, allow_unicode=True)
