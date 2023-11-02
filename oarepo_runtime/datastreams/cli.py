import click
from flask import current_app
from flask.cli import with_appcontext

from oarepo_runtime.cli import oarepo
from oarepo_runtime.datastreams.fixtures import dump_fixtures, load_fixtures
from oarepo_runtime.datastreams.types import StatsKeepingDataStreamCallback


@oarepo.group()
def fixtures():
    """Load and dump fixtures"""


@fixtures.command()
@click.argument("fixture_dir", required=False)
@click.option("--include", multiple=True)
@click.option("--exclude", multiple=True)
@click.option("--system-fixtures/--no-system-fixtures", default=True, is_flag=True)
@click.option("--verbose", is_flag=True)
@click.option(
    "--bulk/--no-bulk",
    is_flag=True,
    default=True,
    help="Use bulk indexing (that is, delay indexing)",
)
@click.option(
    "--bulk-size",
    default=100,
    help="Size for bulk indexing - this number of records "
    "will be committed in a single transaction and indexed together",
)
@with_appcontext
def load(
    fixture_dir=None,
    include=None,
    exclude=None,
    system_fixtures=None,
    verbose=False,
    bulk=True,
    bulk_size=100,
):
    """Loads fixtures"""

    callback = StatsKeepingDataStreamCallback(log_error_entry=verbose)

    with current_app.wsgi_app.mounts["/api"].app_context():
        load_fixtures(
            fixture_dir,
            _make_list(include),
            _make_list(exclude),
            system_fixtures=system_fixtures,
            callback=callback,
            batch_size=bulk_size,
        )
        _show_stats(callback, "Load fixtures")


@fixtures.command()
@click.option("--include", multiple=True)
@click.option("--exclude", multiple=True)
@click.argument("fixture_dir", required=True)
@click.option("--verbose", is_flag=True)
@with_appcontext
def dump(fixture_dir, include, exclude, verbose):
    """Dump fixtures"""
    callback = StatsKeepingDataStreamCallback(log_error_entry=verbose)

    with current_app.wsgi_app.mounts["/api"].app_context():
        dump_fixtures(fixture_dir, _make_list(include), _make_list(exclude))
        _show_stats(callback, "Dump fixtures")


def _make_list(lst):
    return [
        item.strip() for lst_item in lst for item in lst_item.split(",") if item.strip()
    ]


def _show_stats(callback: StatsKeepingDataStreamCallback, title: str):
    print(f"{title} stats:")
    print(callback.stats())
