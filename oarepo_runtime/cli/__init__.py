# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""OAREPO Runtime CLI module."""

from __future__ import annotations

from importlib.metadata import entry_points

import click

from .fingerprint import fingerprint
from .permissions import list_permissions
from .search import init as search_init  # noqa just to register it


@click.group
def oarepo() -> None:
    """OARepo commands. See invenio oarepo --help for details."""


oarepo.add_command(fingerprint)


@oarepo.group
def permissions() -> None:
    """Permission commands."""


permissions.add_command(list_permissions, name="list")

# register additional commands to the oarepo group
for ep in entry_points(group="oarepo.cli"):
    oarepo.add_command(ep.load())  # pragma: nocover
