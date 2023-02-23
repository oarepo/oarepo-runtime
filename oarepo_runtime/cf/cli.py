import click
from flask.cli import with_appcontext

from oarepo_runtime.cli import oarepo

from .mappings import prepare_cf_indices


@oarepo.group()
def cf():
    """Custom fields commands."""


@cf.command(name="init", help="Prepare custom fields in indices")
@click.option(
    "-f",
    "--field-name",
    "field_names",
    type=str,
    required=False,
    multiple=True,
    help="A custom field name to create. If not provided, all custom fields will be created.",
)
@with_appcontext
def init(field_names):
    prepare_cf_indices(field_names)
