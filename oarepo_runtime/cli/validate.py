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
        data = yaml.safe_load(StringIO(file_content))

    loaded = schema().load(data)
    click.secho("Marshmallow validation has been successful", fg="green")

    rec: Record = config.record_cls(loaded)

    # Run pre create extensions to check vocabularies
    try:
        with db.session.begin_nested():
            for e in rec._extensions:
                e.pre_commit(rec)
            raise CheckOk()
    except CheckOk:
        click.secho("Pre-commit hook has been successful", fg="green")

    if verbose:
        yaml.safe_dump(loaded, sys.stdout, allow_unicode=True)
