from typing import Iterable, List
import click
from flask.cli import with_appcontext
from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.records.config import RecordServiceConfig
from invenio_records_resources.services.records.service import RecordService
from invenio_records.dumpers import SearchDumper
from invenio_records_resources.services.custom_fields import BaseCF
from invenio_records_resources.records.dumpers import CustomFieldsDumperExt
from invenio_records_resources.services.custom_fields.validate import (
    validate_custom_fields,
)
from .mappings import Mapping
from flask import current_app
from invenio_search.engine import dsl, search
from invenio_search.utils import build_alias_name
from invenio_search import current_search_client

from oarepo_runtime.cli import oarepo
from .mappings import prepare_cf_indices


@oarepo.group()
def cf():
    """Custom fields commands."""


@cf.command(name="prepare", help="Prepare custom fields in indices")
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
def prepare(field_names):
    prepare_cf_indices(field_names)
