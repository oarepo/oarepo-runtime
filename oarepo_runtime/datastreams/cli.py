import click

from oarepo_runtime.cli import oarepo
from oarepo_runtime.datastreams.fixtures import dump_fixtures, load_fixtures


@oarepo.group()
def fixtures():
    """Load and dump fixtures"""


@fixtures.command()
@click.argument("fixture_dir", required=False)
@click.option("--include", multiple=True)
@click.option("--exclude", multiple=True)
def load(fixture_dir=None, include=None, exclude=None):
    """Loads fixtures"""
    load_fixtures(fixture_dir, _make_list(include), _make_list(exclude))


@fixtures.command()
@click.option("--include", multiple=True)
@click.option("--exclude", multiple=True)
@click.argument("fixture_dir", required=True)
def dump(fixture_dir, include, exclude):
    """Dump fixtures"""
    dump_fixtures(fixture_dir, _make_list(include), _make_list(exclude))


def _make_list(lst):
    return [
        item.strip() for lst_item in lst for item in lst_item.split(",") if item.strip()
    ]
