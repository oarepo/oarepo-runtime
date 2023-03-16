from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, SystemProcess


class ReadOnlyPermissionPolicy(RecordPermissionPolicy):
    """record policy for read only repository"""

    can_search = [SystemProcess(), AnyUser()]
    can_read = [SystemProcess(), AnyUser()]
    can_create = [SystemProcess()]
    can_update = [SystemProcess()]
    can_delete = [SystemProcess()]
    can_manage = [SystemProcess()]

    can_create_files = [SystemProcess()]
    can_set_content_files = [SystemProcess()]
    can_get_content_files = [AnyUser(), SystemProcess()]
    can_commit_files = [SystemProcess()]
    can_read_files = [AnyUser(), SystemProcess()]
    can_update_files = [SystemProcess()]
    can_delete_files = [SystemProcess()]

    can_edit = [SystemProcess()]
    can_new_version = [SystemProcess()]
    can_search_drafts = [SystemProcess()]
    can_read_draft = [SystemProcess()]
    can_update_draft = [SystemProcess()]
    can_delete_draft = [SystemProcess()]
    can_publish = [SystemProcess()]
    can_draft_create_files = [SystemProcess()]
    can_draft_set_content_files = [SystemProcess()]
    can_draft_get_content_files = [SystemProcess()]
    can_draft_commit_files = [SystemProcess()]
    can_draft_read_files = [SystemProcess()]
    can_draft_update_files = [SystemProcess()]


class EveryonePermissionPolicy(RecordPermissionPolicy):
    """record policy for read only repository"""

    can_search = [SystemProcess(), AnyUser()]
    can_read = [SystemProcess(), AnyUser()]
    can_create = [SystemProcess(), AnyUser()]
    can_update = [SystemProcess(), AnyUser()]
    can_delete = [SystemProcess(), AnyUser()]
    can_manage = [SystemProcess(), AnyUser()]

    can_create_files = [SystemProcess(), AnyUser()]
    can_set_content_files = [SystemProcess(), AnyUser()]
    can_get_content_files = [SystemProcess(), AnyUser()]
    can_commit_files = [SystemProcess(), AnyUser()]
    can_read_files = [SystemProcess(), AnyUser()]
    can_update_files = [SystemProcess(), AnyUser()]
    can_delete_files = [SystemProcess(), AnyUser()]

    can_edit = [AnyUser()]
    can_new_version = [AnyUser()]
    can_search_drafts = [AnyUser()]
    can_read_draft = [AnyUser()]
    can_update_draft = [AnyUser()]
    can_delete_draft = [AnyUser()]
    can_publish = [AnyUser()]
    can_draft_create_files = [AnyUser()]
    can_draft_set_content_files = [AnyUser()]
    can_draft_get_content_files = [AnyUser()]
    can_draft_commit_files = [AnyUser()]
    can_draft_read_files = [AnyUser()]
    can_draft_update_files = [AnyUser()]
