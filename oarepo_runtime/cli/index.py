import sys

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records_resources.proxies import current_service_registry
from invenio_search.proxies import current_search
from werkzeug.utils import ImportStringError, import_string

from .base import oarepo


@oarepo.group()
def index():
    "OARepo indexing addons"


@index.command()
@with_appcontext
def init():
    """Create all indices that do not exist yet. This is like 'invenio index init' but does not throw an exception if some indices already exist"""

    click.secho("Creating indexes...", fg="green", bold=True, file=sys.stderr)
    with click.progressbar(
        current_search.create(ignore=[400], ignore_existing=True),
        length=len(current_search.mappings),
    ) as bar:
        for name, response in bar:
            bar.label = name


@index.command()
@with_appcontext
@click.argument("model")
def create(model):
    """Create a single index. The parameter is a service name or python path of the record class"""
    record = record_or_service(model)
    index_name = record.index._name
    index_result, alias_result = current_search.create_index(index_name, ignore=[])
    print(index_name, index_result, alias_result)


def record_or_service(model):
    record = record_or_service(model)
    try:
        service = current_service_registry.get(model)
    except KeyError:
        service = None
    if service:
        record = service.config.record_cls
    else:
        try:
            record = import_string(model)
        except ImportStringError:
            click.secho(
                "Service or model not found. Known services: ",
                fg="red",
                bold=True,
                file=sys.stderr,
            )
            for svc in sorted(current_service_registry._services):
                click.secho(f"    {svc}", file=sys.stderr)
            sys.exit(1)
    return record


@index.command()
@with_appcontext
@click.argument("model", required=False)
def reindex(model):
    if not model:
        services = current_service_registry._services.keys()
    else:
        services = [model]
    for service_id in services:
        click.secho(f"Preparing to index {service_id}", file=sys.stderr)

        service = current_service_registry.get(service_id)
        record_class = service.config.record_cls
        try:
            id_generator = (
                x[0]
                for x in db.session.query(record_class.model_cls.id).filter(
                    record_class.model_cls.is_deleted.is_(False)
                )
            )
        except Exception as e:
            click.secho(
                f"Could not get record ids for {service_id}, exception {e}",
                file=sys.stderr,
            )
            continue

        click.secho(f"Indexing {service_id}", file=sys.stderr)
        ids = list(id_generator)
        for rec_id in ids:
            record = record_class.get_record(rec_id)
            service.indexer.index(record)
        service.indexer.refresh()
        click.secho(
            f"Indexing {service_id} finished, indexed {len(ids)} records",
            file=sys.stderr,
        )
