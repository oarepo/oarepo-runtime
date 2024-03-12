import click
import tqdm
from flask import current_app
from flask.cli import with_appcontext

from oarepo_runtime.cli import oarepo
from oarepo_runtime.datastreams import SynchronousDataStream
from oarepo_runtime.datastreams.asynchronous import AsynchronousDataStream
from oarepo_runtime.datastreams.fixtures import (
    FixturesCallback,
    dump_fixtures,
    fixtures_asynchronous_callback,
    load_fixtures,
)
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
@click.option("--on-background", is_flag=True)
@click.option(
    "--bulk-size",
    default=100,
    type=int,
    help="Size for bulk indexing - this number of records "
    "will be committed in a single transaction and indexed together",
)
@click.option("--batch-size", help="Alias for --bulk-size", type=int)
@with_appcontext
def load(
    fixture_dir=None,
    include=None,
    exclude=None,
    system_fixtures=None,
    verbose=False,
    bulk_size=100,
    on_background=False,
    batch_size=None,
):
    """Loads fixtures"""
    if batch_size:
        bulk_size = batch_size
    if not on_background:
        callback = TQDMCallback(verbose=verbose)
    else:
        callback = fixtures_asynchronous_callback.s()

    if fixture_dir:
        system_fixtures = False

    with current_app.wsgi_app.mounts["/api"].app_context():
        load_fixtures(
            fixture_dir,
            _make_list(include),
            _make_list(exclude),
            system_fixtures=system_fixtures,
            callback=callback,
            batch_size=bulk_size,
            datastreams_impl=(
                AsynchronousDataStream if on_background else SynchronousDataStream
            ),
        )
        if not on_background:
            _show_stats(callback, "Load fixtures")


@fixtures.command()
@click.option("--include", multiple=True)
@click.option("--exclude", multiple=True)
@click.argument("fixture_dir", required=True)
@click.option("--verbose", is_flag=True)
@with_appcontext
def dump(fixture_dir, include, exclude, verbose):
    """Dump fixtures"""
    callback = TQDMCallback(verbose=verbose)

    with current_app.wsgi_app.mounts["/api"].app_context():
        dump_fixtures(fixture_dir, _make_list(include), _make_list(exclude))
        _show_stats(callback, "Dump fixtures")


def _make_list(lst):
    return [
        item.strip() for lst_item in lst for item in lst_item.split(",") if item.strip()
    ]


def _show_stats(callback: StatsKeepingDataStreamCallback, title: str):
    print("\n\n")
    print(f"{title} stats:")
    print(callback.stats())


class TQDMCallback(FixturesCallback):
    def __init__(self, message_prefix="Loading ", verbose=False):
        super().__init__()
        self._tqdm = tqdm.tqdm(unit=" item(s)")
        self._message_prefix = message_prefix
        self._verbose = verbose

    def fixture_started(self, fixture_name):
        self._tqdm.set_description(f"{self._message_prefix}{fixture_name} running")

    def fixture_finished(self, fixture_name):
        self._tqdm.set_description(f"{self._message_prefix}{fixture_name} finished")

    def batch_finished(self, batch):
        super().batch_finished(batch)
        self._tqdm.update(len(batch.entries))
        for err in batch.errors:
            self._tqdm.write("Failed batch: {}: {}".format(err, batch))
        if self._verbose:
            for entry in batch.entries:
                if entry.errors:
                    self._tqdm.write("Failed entry: {}".format(entry))

    def reader_error(self, reader, exception):
        super().reader_error(reader, exception)
        self._tqdm.write("Reader error:{}: {}".format(reader, exception))

    def transformer_error(self, batch, transformer, exception):
        super().transformer_error(batch, transformer, exception)
        self._tqdm.write("Transformer error: {}: {}".format(transformer, exception))

    def writer_error(self, batch, writer, exception):
        super().writer_error(batch, writer, exception)
        self._tqdm.write("Writer error: {}: {}".format(writer, exception))
