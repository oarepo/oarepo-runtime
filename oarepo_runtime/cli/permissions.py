# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""OARepo extensions to list user permissions."""

from __future__ import annotations

from typing import TYPE_CHECKING, cast

import click
from flask import g
from flask.cli import with_appcontext
from flask_login import current_user
from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime import current_runtime
from oarepo_runtime.services.permission_explainer import explain, format_explanation
from oarepo_runtime.typing import record_from_result

if TYPE_CHECKING:
    from invenio_communities.communities.services.service import CommunityService
    from invenio_drafts_resources.services.records.service import RecordService
    from invenio_records_permissions import RecordPermissionPolicy
    from invenio_records_resources.records import Record

# Maybe allow user passing file with data (for cases create permission depends on data)


def read_community(svc: CommunityService, slug: str) -> Record:
    """Read a community record identified by its slug.

    Communities are addressed by a human-readable slug rather than a uuid, and
    they have no draft variant, so they can not go through the generic
    read_draft/read fallback used for other models.
    """
    return record_from_result(svc.read(system_identity, slug))


@click.command()
@click.argument("model_name", required=True)
@click.argument("user_email", required=True)
@click.argument("record_id", required=False)
@click.option("--detailed", is_flag=True, help="Show detailed permission information")
@click.option("--action", required=False, help="Filter by action (for example, create or read)")
@with_appcontext
def list_permissions(
    model_name: str,
    user_email: str,
    record_id: str | None = None,
    detailed: bool = False,
    action: str | None = None,
) -> None:
    """Check permissions for a given user and record.

    MODEL_NAME: the name of the model to check permissions for
    USER_EMAIL: the email of the user to check permissions for
    RECORD_ID: the ID of the record to check permissions for
    """
    with current_runtime.login_user(user_email):
        click.secho()
        click.secho("User identity:", fg="cyan", bold=True)
        click.secho(f"  - {g.identity.id}")
        for provide in g.identity.provides:
            click.secho(f"  - {provide}")

        click.secho()
        click.secho("Global roles:", fg="cyan", bold=True)
        if current_user.roles:
            for role in current_user.roles:
                click.secho(f"  - {role}")
        else:
            click.secho("  - No roles assigned")
        if model_name in current_runtime.models:
            svc = cast("RecordService", current_runtime.models[model_name].service)
        else:
            svc = cast("RecordService", current_service_registry.get(model_name))

        from invenio_communities.communities.services.service import CommunityService

        if record_id is None:
            rec = None
        elif isinstance(svc, CommunityService):
            rec = read_community(svc, record_id)
        else:
            try:
                rec = record_from_result(svc.read_draft(system_identity, record_id))
            except Exception:  # noqa BLE001
                rec = record_from_result(svc.read(system_identity, record_id))

        click.secho()
        click.secho("Permissions:", fg="cyan", bold=True)
        click.secho()
        print_permission_policy(svc.config.permission_policy_cls, rec, detailed, action)


def print_permission_policy(
    permission_policy_cls: type[RecordPermissionPolicy],
    rec: Record | None,
    detailed: bool,
    restrict_to_action: str | None = None,
    indent: str = "",
) -> None:
    """Print the permission policy for the given record."""
    for member in dir(permission_policy_cls):
        if not member.startswith("can_"):
            continue
        if restrict_to_action and member[4:] != restrict_to_action:
            continue
        policy = permission_policy_cls(member[4:], record=rec)
        generators = [type(x).__name__ for x in getattr(policy, member)]
        try:
            allows = policy.allows(g.identity)
            icon = "✅" if allows else "❌"
            click.secho(
                f"{indent}{icon} {member[4:]:<30}: {', '.join(generators)}",
                fg="green" if allows else "red",
            )
        except Exception as exc:  # noqa: BLE001
            click.secho(
                f"{indent}⚠️  {member[4:]:<30}: {', '.join(generators)}: {type(exc).__name__}: {exc}", fg="yellow"
            )
        if detailed:
            for permission_generator in getattr(policy, member):
                click.secho(
                    format_explanation(explain(g.identity, policy, permission_generator), indent=indent + "    ")
                )
