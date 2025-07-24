from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    SystemProcess,
)

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
    can_list_files = [SystemProcess(), AnyUser()]
    can_manage_files = [SystemProcess(), AnyUser()]

    can_edit = [SystemProcess(), AnyUser()]
    can_new_version = [SystemProcess(), AnyUser()]
    can_search_drafts = [SystemProcess(), AnyUser()]
    can_read_draft = [SystemProcess(), AnyUser()]
    can_search_versions = [SystemProcess(), AnyUser()]
    can_update_draft = [SystemProcess(), AnyUser()]
    can_delete_draft = [SystemProcess(), AnyUser()]
    can_publish = [SystemProcess(), AnyUser()]
    can_draft_create_files = [SystemProcess(), AnyUser()]
    can_draft_set_content_files = [SystemProcess(), AnyUser()]
    can_draft_get_content_files = [SystemProcess(), AnyUser()]
    can_draft_commit_files = [SystemProcess(), AnyUser()]
    can_draft_read_files = [SystemProcess(), AnyUser()]
    can_draft_update_files = [SystemProcess(), AnyUser()]
    can_draft_delete_files = [SystemProcess(), AnyUser()]

    can_add_community = [SystemProcess(), AnyUser()]
    can_remove_community = [SystemProcess(), AnyUser()]

    can_read_deleted = [SystemProcess(), AnyUser()]
    can_manage_record_access = [SystemProcess(), AnyUser()]
    can_lift_embargo = [SystemProcess(), AnyUser()]
