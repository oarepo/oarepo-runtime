#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Everyone permissions."""

from __future__ import annotations

from typing import ClassVar

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import (
    AnyUser,
    SystemProcess,
)


class EveryonePermissionPolicy(RecordPermissionPolicy):
    """Record policy for read-only repository."""

    can_search: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_read: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_create: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_update: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_delete: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_manage: ClassVar[list] = [SystemProcess(), AnyUser()]

    can_create_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_set_content_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_get_content_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_commit_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_read_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_update_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_delete_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_list_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_manage_files: ClassVar[list] = [SystemProcess(), AnyUser()]

    can_edit: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_new_version: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_search_drafts: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_read_draft: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_search_versions: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_update_draft: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_delete_draft: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_publish: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_draft_create_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_draft_set_content_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_draft_get_content_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_draft_commit_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_draft_read_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_draft_update_files: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_draft_delete_files: ClassVar[list] = [SystemProcess(), AnyUser()]

    can_add_community: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_remove_community: ClassVar[list] = [SystemProcess(), AnyUser()]

    can_read_deleted: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_manage_record_access: ClassVar[list] = [SystemProcess(), AnyUser()]
    can_lift_embargo: ClassVar[list] = [SystemProcess(), AnyUser()]
