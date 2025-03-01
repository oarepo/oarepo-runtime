from typing import get_type_hints

import click

from oarepo_runtime.info.permissions.debug import add_debugging

from .base import permissions


@permissions.command(name="list")
@click.option("--workflow", "-w", help="Workflow name")
@click.option("--community", "-c", help="Community name")
@click.option("--service", "-s", help="Service name")
def list_permissions(workflow, community, service):
    """List all permissions for a given workflow, community or service."""
    # intentionally import here to enable oarepo-runtime to be used
    # without oarepo-workflows and oarepo-communities
    from invenio_communities.communities.records.api import Community
    from invenio_communities.communities.records.models import CommunityMetadata
    from oarepo_workflows.proxies import current_oarepo_workflows

    if workflow:
        wf = current_oarepo_workflows.record_workflows[workflow]
        permission_policy = wf.permission_policy_cls
    elif community:
        community_db = CommunityMetadata.query.filter_by(slug=community).one()
        community_obj = Community(community_db.data, model=community_db)
        workflow = community_obj["custom_fields"].get("workflow", "default")
        wf = current_oarepo_workflows.record_workflows[workflow]
        permission_policy = wf.permission_policy_cls
    elif service:
        from invenio_records_resources.proxies import current_service_registry

        swc = current_service_registry.get(service)
        permission_policy = swc.config.permission_policy_cls
    else:
        raise click.UsageError(
            "You must specify either --workflow, --community or --service."
        )

    add_debugging()

    p = permission_policy("read")

    for action_name in dir(permission_policy):
        if not action_name.startswith("can_"):
            continue
        action_permission_generators = getattr(p, action_name)
        debugs = []
        for x in action_permission_generators:
            debugs.append(x.to_debug_dict())

        print("")
        print(f"## {action_name}")
        print(get_permission_documentation(permission_policy, action_name))
        for perm in debugs:
            print_permission_markdown(perm)


def is_simple_dict(d):
    return all(isinstance(v, (str, int, float, bool)) for v in d.values())


def format_simple_dict_values(d):
    # returns k=v, k=v, ...
    return ", ".join(f"{k}={v}" for k, v in d.items())


def print_permission_markdown(p, level=0):
    for k, v in p.items():
        prologue = "  " * level + f"- {k}"
        if v is None or v == {} or v == []:
            print(prologue)
            continue
        elif isinstance(v, dict):
            if is_simple_dict(v):
                print(f"{prologue}: {format_simple_dict_values(v)}")
            else:
                print(prologue)
                print_permission_markdown(v, level + 1)
        elif isinstance(v, list):
            print(prologue)
            for x in v:
                print_permission_markdown(x, level + 1)
        else:
            print("  " * (level + 1) + f"{v}")


def get_permission_documentation(policy, permission_can_name):
    type_hints = get_type_hints(policy, include_extras=True)
    annotation = type_hints.get(permission_can_name)
    if annotation:
        for md in annotation.__metadata__:
            if isinstance(md, str):
                return md
    ret = default_permissions_documentation.get(permission_can_name, "")
    return "\n".join(x.strip() for x in ret.split("\n"))


default_permissions_documentation = {
    # records
    "can_create": """
        Grants users the ability to create new records in the 
        repository, often assigned to roles like submitters, owners, or curators.
        The result of this action is typically a draft record.
    """,
    "can_read": """
        Allows users to view or access records, with access 
        possibly dependent on the record's state (e.g., draft or published) and the 
        user's role.
    """,
    "can_read_deleted": """
        Permission to view or access records, including soft-deleted ones. This 
        permission is used to filter search results. It should include an 
        `IfRecordDeleted` permission generator, which grants access to deleted 
        records to a subset of users (e.g., owners, curators, etc.). For 
        `service.read`, this permission is applied when record is deleted and 
        `include_deleted` is passed; otherwise, a `RecordDeletedException` is raised.
    """,
    "can_search": """
        Grants users the ability to search for records within the 
        repository, typically available to all users. The search results are
        filtered based on the can_read_deleted permission for published records (/api/datasets)
        and the can_read_draft permission for draft records (/api/user/datasets).
    """,
    "can_update": """
        Grants users the ability to update or modify published records.
        In NRP repositories, this is normally disabled as updates are performed
        on draft records, which are then published.
    """,
    "can_delete": """
        Grants users the ability to delete records, often restricted 
        to owners, curators, or specific roles, and dependent on the record's 
        state (e.g., draft). For published records, the deletion is performed
        via a specialized request, not directly.
    """,
    "can_new_version": """
        Allows users to create a new version of a record. In NRP,
        this is not used directly but always via a request, which is mostly
        auto-approved.
    """,
    "can_edit": """
        Grants users the ability to modify the metadata of a record. In NRP, this
        is not used directly but always via a request, which is mostly auto-approved.
    """,
    "can_manage": """
        Grants users the ability to manage records. Currently it is used just
        for reindexing records with latest version first (reindex_latest_first)
        service call, not mapped to REST API.
    """,
    "can_manage_record_access": """
        Grants users the ability to manage record access.
    """,
    # draft records
    "can_read_draft": """
        Enables users to view or access draft records, typically equivalent to 
        the general 'can_read' permission but specific to drafts.
    """,
    "can_delete_draft": """
        Allows users to delete draft records, typically equivalent to the general 
        'can_delete' permission but specific to drafts.
    """,
    "can_update_draft": """
        Allows users to update draft records. It is typically granted to record
        owner, but can be restricted by the record status (such as records submitted
        to review being locked).
    """,
    "can_publish": """
        Grants users the ability to publish records, making them publicly 
        available or finalizing their state. In NRP repositories, this is
        not used directly but always via a request.
    """,
    # files
    "can_read_files": """
        Grants users the ability to view or access file metadata associated with records, 
        with access dependent on the record's state and the user's role.
    """,
    "can_create_files": """
        Enables users to create new files within published records in the repository.
        Normally disabled as files are created in draft records and then published.
    """,
    "can_delete_files": """
        Enables users to delete files associated with published records in the repository.
        Normally disabled as files can not be deleted from published records.
    """,
    "can_update_files": """
        Enables users to update or modify files within published records in the repository.
        Normally disabled as files are updated in draft records and then published.
    """,
    "can_commit_files": """
        Allows users to finalize file upload to published records in the repository.
        Normally disabled as files are uploaded to draft records and then published.
    """,
    "can_get_content_files": """
        Allows users to access or retrieve the content of files on records published 
        in the repository, with access depending on the record's state and the user's role.
    """,
    "can_manage_files": """
        Grants users the ability to manage files (that is, change if the files are
        required on the record or not).
    """,
    "can_read_deleted_files": """
        Allows users to view or access files associated with deleted records, 
        often restricted to specific conditions.
    """,
    "can_set_content_files": """
        Enables users to upload files to published records. Normally disabled as files
        are uploaded to draft records and then published.
    """,
    # draft files
    "can_draft_read_files": """
        Allows users to view or access file metadata associated with draft records,
        typically equivalent to the general 'can_read_files' permission but specific
        to drafts.
    """,
    "can_draft_create_files": """
        Allows users to create files specifically for draft records.
    """,
    "can_draft_get_content_files": """
        Allows users to access or retrieve the content of files on draft records.
    """,
    "can_draft_set_content_files": """
        Allows users to upload files to draft records.
    """,
    "can_draft_commit_files": """
        Allows users to finalize file upload to draft records.
    """,
    "can_draft_update_files": """
        Allows users to update or modify files within draft records.
    """,
    "can_draft_delete_files": """
        Allows users to delete files associated with draft records.
    """,
    # misc
    "can_create_or_update_many": """
        Allows bulk creation or updating of multiple records or files.
        Not used at the moment.
    """,
}
