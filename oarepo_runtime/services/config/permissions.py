# mypy: disable-error-code="assignment"
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

from invenio_records_permissions import RecordPermissionPolicy
from invenio_records_permissions.generators import AnyUser, Generator, SystemProcess

type GeneratorList = tuple[Generator, ...]


class EveryonePermissionPolicy(RecordPermissionPolicy):
    """Record policy for read-only repository."""

    can_search: GeneratorList = (SystemProcess(), AnyUser())
    can_read: GeneratorList = (SystemProcess(), AnyUser())
    can_create: GeneratorList = (SystemProcess(), AnyUser())
    can_update: GeneratorList = (SystemProcess(), AnyUser())
    can_delete: GeneratorList = (SystemProcess(), AnyUser())
    can_manage: GeneratorList = (SystemProcess(), AnyUser())

    can_create_files: GeneratorList = (SystemProcess(), AnyUser())
    can_set_content_files: GeneratorList = (SystemProcess(), AnyUser())
    can_get_content_files: GeneratorList = (SystemProcess(), AnyUser())
    can_commit_files: GeneratorList = (SystemProcess(), AnyUser())
    can_read_files: GeneratorList = (SystemProcess(), AnyUser())
    can_update_files: GeneratorList = (SystemProcess(), AnyUser())
    can_delete_files: GeneratorList = (SystemProcess(), AnyUser())
    can_list_files: GeneratorList = (SystemProcess(), AnyUser())
    can_manage_files: GeneratorList = (SystemProcess(), AnyUser())

    can_edit: GeneratorList = (SystemProcess(), AnyUser())
    can_new_version: GeneratorList = (SystemProcess(), AnyUser())
    can_search_drafts: GeneratorList = (SystemProcess(), AnyUser())
    can_read_draft: GeneratorList = (SystemProcess(), AnyUser())
    can_search_versions: GeneratorList = (SystemProcess(), AnyUser())
    can_update_draft: GeneratorList = (SystemProcess(), AnyUser())
    can_delete_draft: GeneratorList = (SystemProcess(), AnyUser())
    can_publish: GeneratorList = (SystemProcess(), AnyUser())
    can_draft_create_files: GeneratorList = (SystemProcess(), AnyUser())
    can_draft_set_content_files: GeneratorList = (SystemProcess(), AnyUser())
    can_draft_get_content_files: GeneratorList = (SystemProcess(), AnyUser())
    can_draft_commit_files: GeneratorList = (SystemProcess(), AnyUser())
    can_draft_read_files: GeneratorList = (SystemProcess(), AnyUser())
    can_draft_update_files: GeneratorList = (SystemProcess(), AnyUser())
    can_draft_delete_files: GeneratorList = (SystemProcess(), AnyUser())

    can_add_community: GeneratorList = (SystemProcess(), AnyUser())
    can_remove_community: GeneratorList = (SystemProcess(), AnyUser())

    can_read_deleted: GeneratorList = (SystemProcess(), AnyUser())
    can_manage_record_access: GeneratorList = (SystemProcess(), AnyUser())
    can_lift_embargo: GeneratorList = (SystemProcess(), AnyUser())
