#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from invenio_search.cli import destroy

from oarepo_runtime.cli.permissions import list_permissions
from oarepo_runtime.cli.search import init


def test_cli(app, search):
    """Test CLI commands."""
    runner = app.test_cli_runner()
    result = runner.invoke(destroy, "--yes-i-know")
    result = runner.invoke(init)
    assert result.exit_code == 0


def test_permission_cli(app, search, users):
    """Test permission CLI commands."""
    runner = app.test_cli_runner()
    result = runner.invoke(list_permissions, ["vocabularies", users[0].user.email, "--detailed"])
    assert result.exit_code == 0
