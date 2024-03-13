import sys
from io import StringIO

import click
import yaml
from flask.cli import with_appcontext
from invenio_db import db
from invenio_records_resources.proxies import current_service_registry
from invenio_search.proxies import current_search
from werkzeug.utils import ImportStringError, import_string

try:
    from tqdm import tqdm
except ImportError:

    def tqdm(generator):
        yield from generator


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
    # TODO: is this still used (maybe from somewhere else?)
    try:
        service = current_service_registry.get(model)
    except KeyError:
        service = None
    if service and getattr(service, "config", None):
        record = getattr(service.config, "record_cls", None)
    else:
        try:
            record = import_string(model)
        except ImportStringError:
            record = None

    if record is None:
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


def model_records_generator(model_class):
    try:
        for x in db.session.query(model_class.model_cls.id).filter(
            model_class.model_cls.is_deleted.is_(False)
        ):
            rec_id = x[0]
            yield model_class.get_record(rec_id)
    except Exception as e:
        click.secho(f"Could not index {model_class}: {e}", fg="red", file=sys.stderr)


@index.command()
@with_appcontext
@click.argument("model", required=False)
@click.option("--bulk-size", required=False, default=5000, type=int)
@click.option("--verbose/--no-verbose", default=False)
def reindex(model, bulk_size, verbose):
    if not model:
        services = current_service_registry._services.keys()
    else:
        services = [model]
    for service_id in services:
        click.secho(f"Preparing to index {service_id}", file=sys.stderr)

        service = current_service_registry.get(service_id)
        record_class = getattr(service.config, "record_cls", None)

        id_generators = []

        if record_class and hasattr(service, "indexer"):
            try:
                id_generators.append(model_records_generator(record_class))
            except Exception as e:
                click.secho(
                    f"Could not get record ids for {service_id}, exception {e}",
                    file=sys.stderr,
                )

        draft_class = getattr(service.config, "draft_cls", None)

        if draft_class and hasattr(service, "indexer"):
            try:
                id_generators.append(model_records_generator(draft_class))
            except Exception as e:
                click.secho(
                    f"Could not get draft record ids for {service_id}, exception {e}",
                    file=sys.stderr,
                )

        click.secho(f"Indexing {service_id}", file=sys.stderr)
        count = 0
        errors = 0
        for gen in id_generators:
            for bulk in generate_bulk_data(gen, service.indexer, bulk_size=bulk_size):
                index_result = service.indexer.client.bulk(bulk)
                count += len(bulk) // 2

                for index_item_result in index_result["items"]:
                    result = index_item_result["index"]
                    if result["status"] != 200:
                        errors += 1
                        click.secho(
                            f"Error indexing record with id {result['_id']}",
                            fg="red",
                            file=sys.stderr,
                        )
                        click.secho(
                            dump_yaml(result.get("error")), fg="red", file=sys.stderr
                        )
                        if verbose:
                            click.secho("Record:", file=sys.stderr)
                            rec = [
                                bulk[idx + 1]
                                for idx in range(0, len(bulk), 2)
                                if bulk[idx]["index"]["_id"] == result["_id"]
                            ]
                            if rec:
                                click.secho(dump_yaml(rec[0]))
                            else:
                                click.secho("<no record found>")

        if count:
            service.indexer.refresh()

        if errors:
            click.secho(
                f"Indexing {service_id} failed, indexed {count - errors} records, failed {errors} records.",
                fg="red",
                file=sys.stderr,
            )
            if not verbose:
                click.secho("Run with --verbose to see information about the errors")
        else:
            click.secho(
                f"Indexing {service_id} finished, indexed {count} records",
                fg="green",
                file=sys.stderr,
            )


def generate_bulk_data(record_generator, record_indexer, bulk_size):
    data = []
    n = 0
    for record in tqdm(record_generator):
        index = record_indexer.record_to_index(record)
        body = record_indexer._prepare_record(record, index)
        index = record_indexer._prepare_index(index)
        data.append({"index": {"_index": index, "_id": body["uuid"]}})
        data.append(body)
        if len(data) >= bulk_size:
            yield data
            data = []
    if data:
        yield data


def dump_yaml(data):
    io = StringIO()
    yaml.dump(data, io, allow_unicode=True)
    return io.getvalue()
