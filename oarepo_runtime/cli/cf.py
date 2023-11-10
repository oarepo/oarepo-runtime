from flask.cli import with_appcontext

from oarepo_runtime.cli import oarepo
from oarepo_runtime.services.custom_fields.mappings import prepare_cf_indices


@oarepo.group()
def cf():
    """Custom fields commands."""


@cf.command(name="init", help="Prepare custom fields in indices")
@with_appcontext
def init():
    prepare_cf_indices()
