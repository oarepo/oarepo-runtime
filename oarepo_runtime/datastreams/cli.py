import click
from oarepo_runtime.cli import oarepo
from oarepo_runtime.datastreams.fixtures import load_fixtures, dump_fixtures


@oarepo.group()
def fixtures():
    """Load and dump fixtures"""


@fixtures.command()
@click.argument("fixture_dir", required=False)
def load(fixture_dir=None):
    """Loads fixtures"""

    load_fixtures(fixture_dir)


@fixtures.command()
@click.option("--skip", multiple=True)
@click.argument("fixture_dir", required=True)
def dump(fixture_dir, skip):
    """Dump fixtures"""
    skip = [
        item.strip()
        for skip_item in skip
        for item in skip_item.split(",")
        if item.strip()
    ]
    dump_fixtures(fixture_dir, skip)
