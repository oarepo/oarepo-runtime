import json

import click
from invenio_records_permissions.policies.records import RecordPermissionPolicy
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime.info.permissions.debug import add_debugging

from .base import get_user_and_identity, permissions


@permissions.command(name="evaluate")
@click.argument("user_id_or_email")
@click.argument("service_name")
@click.argument("record_id", required=False)
@click.option("--data", "-d", help="Data to pass to the policy check")
@click.option("--explain/--no-explain", default=False)
@click.option("--draft/--published", default=False)
def evaluate_permissions(
    user_id_or_email: str,
    service_name: str,
    record_id: str | None = None,
    data: str | None = None,
    explain: bool = False,
    draft: bool = False,
):
    """Evaluate permissions for a given workflow, community or service."""
    service = current_service_registry.get(service_name)
    user, identity = get_user_and_identity(user_id_or_email)

    over = {}
    if record_id:
        if draft:
            over["record"] = service.config.draft_cls.pid.resolve(
                record_id, registered_only=False
            )
        else:
            over["record"] = service.config.record_cls.pid.resolve(record_id)
    if data:
        over["data"] = json.loads(data)

    if explain:
        over["debug_identity"] = identity
        add_debugging()

    policy_cls = service.config.permission_policy_cls
    click.secho(f"Policy: {policy_cls}")

    for action_name in dir(policy_cls):
        if not action_name.startswith("can_"):
            continue

        policy: RecordPermissionPolicy = policy_cls(action_name[4:], **over)
        if explain:
            click.secho()
            click.secho(f"## {action_name}")
        try:
            if policy.allows(identity):
                click.secho(f"{action_name}: True", fg="green")
            else:
                click.secho(f"{action_name}: False", fg="red")
        except Exception as e:
            click.secho(f"{action_name}: {e}", fg="yellow")
