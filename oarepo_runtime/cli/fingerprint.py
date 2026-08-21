#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Fingerprint of the packages installed in the repository."""

from __future__ import annotations

import click
from flask.cli import with_appcontext

from oarepo_runtime.proxies import current_runtime


@click.command()
@with_appcontext
def fingerprint() -> None:
    """Print the fingerprints of the installed packages."""
    fingerprints = current_runtime.fingerprint
    click.echo(f"major: {fingerprints[0]}, minor: {fingerprints[1]}, patch: {fingerprints[2]}, full: {fingerprints[3]}")
