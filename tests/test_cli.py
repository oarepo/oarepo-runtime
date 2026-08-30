#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_access.permissions import system_identity
from invenio_accounts.proxies import current_datastore
from invenio_records_resources.proxies import current_service_registry
from invenio_search.cli import destroy

from oarepo_runtime import current_runtime
from oarepo_runtime.cli.permissions import list_permissions
from oarepo_runtime.cli.search import init

if TYPE_CHECKING:
    from invenio_accounts.models import Role


def test_cli(app, search):
    """Test CLI commands."""
    runner = app.test_cli_runner()
    result = runner.invoke(destroy, "--yes-i-know")
    result = runner.invoke(init)
    assert result.exit_code == 0


def test_permission_cli(app, db, search, users):
    """Test permission CLI commands."""
    role: Role = current_datastore.create_role(name="test-role", description="Role used in the CLI test")
    current_datastore.add_role_to_user(users[0].user, role)
    current_datastore.commit()

    runner = app.test_cli_runner()
    result = runner.invoke(list_permissions, ["affiliations", users[0].user.email, "--detailed"])
    assert result.exit_code == 0
    assert "test-role" in result.output


def test_permission_cli_with_existing_record(app, db, search_clear, users):
    """Test permission CLI commands when an existing affiliation record id is passed."""
    affiliations_service = current_runtime.models["affiliations"].service
    affiliations_service.create(system_identity, {"id": "cern", "name": "CERN"})

    runner = app.test_cli_runner()
    result = runner.invoke(list_permissions, ["affiliations", users[0].user.email, "cern", "--detailed"])
    assert result.exit_code == 0


def test_permission_cli_with_community_slug(app, db, search_clear, location, users):
    """Communities are not registered in OAREPO_MODELS and are addressed by slug, not uuid."""
    communities_service = current_service_registry.get("communities")
    communities_service.create(
        system_identity,
        {
            "slug": "my-community",
            "access": {"visibility": "public"},
            "metadata": {"title": "My Community"},
        },
    )

    runner = app.test_cli_runner()
    result = runner.invoke(list_permissions, ["communities", users[0].user.email, "my-community", "--detailed"])
    assert result.exit_code == 0
