# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from io import BytesIO

from oarepo_runtime.proxies import current_runtime
from oarepo_runtime.services.config.link_conditions import (
    Condition,
    has_draft,
    has_draft_permission,
    has_permission,
    has_published_record,
    is_draft,
    is_published_record,
)


def test_link_conditions(app, db, search_with_field_mapping, service, search_clear, identity_simple, location):
    rec = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "files": {"enabled": False},
        },
    )
    draft = rec._record  # noqa: SLF001

    context = {"identity": identity_simple}

    assert has_draft_permission("read")(draft, context)
    assert not has_draft_permission("unknown")(draft, context)

    assert has_permission("read")(draft, context)
    assert not has_published_record()(draft, context)
    assert not is_published_record()(draft, context)
    assert is_draft()(draft, context)

    assert has_draft()(draft, context)

    assert (has_draft_permission("read") & has_permission("read"))(draft, context)
    assert not (has_draft_permission("read") & has_draft_permission("unknown"))(draft, context)
    assert (has_draft_permission("read") | has_draft_permission("unknown"))(draft, context)

    rec = service.publish(identity_simple, rec.id)
    record = rec._record  # noqa: SLF001

    assert not has_draft_permission("read")(record, context)
    assert has_permission("read")(record, context)
    assert has_published_record()(record, context)
    assert is_published_record()(record, context)
    assert not is_draft()(record, context)
    assert not has_draft()(record, context)

    rec = service.edit(identity_simple, rec.id)
    draft = rec._record  # noqa: SLF001

    assert has_draft_permission("read")(draft, context)
    assert has_permission("read")(draft, context)
    assert has_published_record()(draft, context)
    assert not is_published_record()(draft, context)
    assert has_draft()(draft, context)

    rec = service.read(identity_simple, record["id"])
    record = rec._record  # noqa: SLF001

    assert has_draft_permission("read")(record, context)
    assert has_permission("read")(record, context)
    assert has_published_record()(record, context)
    assert is_published_record()(record, context)
    assert has_draft()(record, context)

    assert isinstance(~is_published_record(), Condition)
    assert (~is_published_record())(draft, context)
    assert not (~is_published_record())(record, context)
    assert not (~has_draft_permission("read") & has_permission("read"))(draft, context)


def test_link_conditions_with_file_record(app, db, search_with_field_mapping, service, search_clear, identity_simple, location):
    rec = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "files": {"enabled": True},
        },
    )
    draft = rec._record  # noqa: SLF001
    file_service = current_runtime.get_file_service_for_record(draft)
    file_service.init_files(identity_simple, rec.id, data=[{"key": "test.txt"}])
    file_service.set_file_content(identity_simple, rec.id, "test.txt", BytesIO(b"jeej"))
    file_item = file_service.commit_file(identity_simple, rec.id, "test.txt")
    file_record = file_item._file  # noqa: SLF001

    context = {"identity": identity_simple}

    assert has_permission("read")(file_record, context)
