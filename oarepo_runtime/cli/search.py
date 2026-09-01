# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""OARepo extensions to the index command."""

from __future__ import annotations

from importlib import metadata as importlib_metadata

import click
from flask.cli import with_appcontext
from invenio_search.cli import index, search_version_check
from invenio_search.cli import init as original_init


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
    for ep in importlib_metadata.entry_points(group="oarepo.cli.search.init"):
        ep.load()()
