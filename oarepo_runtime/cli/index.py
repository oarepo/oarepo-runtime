import sys

import click
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records_resources.proxies import current_service_registry
from invenio_search.proxies import current_search
from werkzeug.utils import ImportStringError, import_string

from .base import oarepo


@oarepo.group()
def index():
    "OARepo indexing addons"


@index.command(
    help="Create all indices that do not exist yet. "
    "This is like 'invenio index init' but does not throw "
    "an exception if some indices already exist"
)
@with_appcontext
def init():
    click.secho("Creating indexes...", fg="green", bold=True, file=sys.stderr)
    all_indices = list(gather_all_indices())
    new_indices = []
    with click.progressbar(all_indices, label="Checking which indices exist") as bar:
        for name, alias in bar:
            if not current_search.client.indices.exists(alias):
                new_indices.append(name)
    if new_indices:
        with click.progressbar(
            current_search.create(
                ignore=[400], ignore_existing=True, index_list=new_indices
            ),
            length=len(new_indices),
        ) as bar:
            for name, response in bar:
                bar.label = name


def gather_all_indices():
    """Yield index_file, index_name for all indices."""

    # partially copied from invenio-search
    def _build(tree_or_filename, alias=None):
        """Build a list of index/alias actions to perform."""
        for name, value in tree_or_filename.items():
            if isinstance(value, dict):
                yield from _build(value, alias=name)
            else:
                index_result, alias_result = current_search.create_index(
                    name, dry_run=True
                )
                yield name, alias_result[0]

    yield from _build(current_search.active_aliases)


def record_or_service(model):
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

        if not hasattr(service, "indexer"):
            continue

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
