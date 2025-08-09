"""OARepo extensions to the index command."""

from __future__ import annotations

import click
from flask.cli import with_appcontext
from invenio_search.cli import index
from invenio_search.cli import init as original_init
from invenio_search.cli import search_version_check

from oarepo_runtime.services.records.mapping import update_all_records_mappings


@index.command()
@click.option("--force", is_flag=True, default=False)
@with_appcontext
@search_version_check
@click.pass_context
def init(ctx: click.Context, force: bool) -> None:
    """Initialize registered aliases and mappings.

    This command initializes the search indices by creating templates, component templates,
    index templates, and the actual indices. It will also create all dynamic mappings
    defined inside the models.
    """
    ctx.invoke(original_init, force=force)
    update_all_records_mappings()
