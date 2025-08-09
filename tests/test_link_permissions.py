from oarepo_runtime.services.config.link_conditions import (
    has_draft,
    has_draft_permission,
    has_permission,
    has_published_record,
    is_published_record,
)


def test_link_conditions(
    app, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
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

    assert has_draft()(draft, context)

    assert (has_draft_permission("read") & has_permission("read"))(draft, context)
    assert not (has_draft_permission("read") & has_draft_permission("unknown"))(
        draft, context
    )
    assert (has_draft_permission("read") | has_draft_permission("unknown"))(
        draft, context
    )

    rec = service.publish(identity_simple, rec.id)
    record = rec._record  # noqa: SLF001

    assert not has_draft_permission("read")(record, context)
    assert has_permission("read")(record, context)
    assert has_published_record()(record, context)
    assert is_published_record()(record, context)
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
