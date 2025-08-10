#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from oarepo_runtime.records.drafts import get_draft, has_draft


def test_service_flow(
    app, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
    rec = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "unknown": True,
            "files": {"enabled": False},
        },
    )
    assert rec.id is not None

    draft = rec._record  # noqa: SLF001
    assert draft.status == "draft"
    assert rec.errors == [{"field": "unknown", "messages": ["Unknown field."]}]

    assert get_draft(draft) is draft
    assert has_draft(draft)  # draft is itself a draft

    serialized = rec.to_dict()
    assert serialized["metadata"]["title"] == "Test Record"
    assert serialized["result_component"]
    assert rec.to_dict() == serialized

    # TODO: check links & html links

    service.config.draft_cls.index.refresh()

    hits = service.search_drafts(
        identity_simple, params={"facets": {"publication_status": ["draft"]}}
    )
    assert hits.total == 1
    items = list(hits.hits)
    assert len(items) == 1
    assert items[0]["result_component"]
    # TODO: check links & html links

    assert hits.aggregations == {
        "publication_status": {
            "buckets": [
                {"doc_count": 1, "is_selected": True, "key": "draft", "label": "draft"}
            ],
            "label": "",
        }
    }

    hits = service.search_drafts(
        identity_simple, params={"facets": {"publication_status": ["published"]}}
    )
    assert hits.total == 0

    # publish the record

    rec = service.publish(identity_simple, rec.id)
    assert rec.id is not None

    record = rec._record  # noqa: SLF001
    assert record.status == "published"
    assert rec.errors == []
    assert get_draft(record) is None
    assert not has_draft(record)

    service.config.draft_cls.index.refresh()
    service.config.record_cls.index.refresh()

    hits = service.search_drafts(
        identity_simple, params={"facets": {"publication_status": ["draft"]}}
    )
    assert hits.total == 0

    hits = service.search(identity_simple)
    assert hits.total == 1

    items = list(hits.hits)
    assert len(items) == 1
    assert items[0]["result_component"]
    # TODO: check links & html links

    assert hits.aggregations == {
        "publication_status": {
            "buckets": [
                {
                    "doc_count": 1,
                    "is_selected": False,
                    "key": "published",
                    "label": "published",
                }
            ],
            "label": "",
        }
    }
