# SPDX-FileCopyrightText: 2025 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

from __future__ import annotations

from oarepo_runtime.records.drafts import get_draft, has_draft


def test_service_flow(app, db, search_with_field_mapping, service, search_clear, identity_simple, location):
    rec = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "unknown": True,
            "files": {"enabled": False},
        },
    )
    assert rec.id is not None

    draft = rec._record
    assert draft.status == "draft"
    assert rec.errors == [{"field": "unknown", "messages": ["Unknown field."]}]

    assert get_draft(draft) is draft
    assert has_draft(draft)  # draft is itself a draft

    serialized = rec.to_dict()
    assert serialized["metadata"]["title"] == "Test Record"
    assert serialized["result_component"]
    assert rec.to_dict() == serialized

    links = serialized["links"]

    assert links["self"].endswith(f"/api/mocks/{rec.id}/draft")
    assert links["self_html"].endswith(f"/uploads/{rec.id}")

    service.config.draft_cls.index.refresh()

    hits = service.search_drafts(identity_simple, params={"facets": {"publication_status": ["draft"]}})
    assert hits.total == 1
    items = list(hits.hits)
    assert len(items) == 1
    assert items[0]["result_component"]
    links = items[0]["links"]
    assert links["self"].endswith(f"/api/mocks/{rec.id}/draft")
    assert links["self_html"].endswith(f"/uploads/{rec.id}")
    assert links["latest"].endswith(f"/api/mocks/{rec.id}/versions/latest")
    assert links["latest_html"].endswith(f"/mocks/{rec.id}/latest")
    assert links["record"].endswith(f"/api/mocks/{rec.id}")
    assert links["publish"].endswith(f"/api/mocks/{rec.id}/draft/actions/publish")
    assert links["versions"].endswith(f"/api/mocks/{rec.id}/versions")
    assert links["files"].endswith(f"/api/mocks/{rec.id}/draft/files")
    assert "draft" not in links

    assert hits.aggregations == {
        "publication_status": {
            "buckets": [{"doc_count": 1, "is_selected": True, "key": "draft", "label": "draft"}],
            "label": "",
        }
    }

    hits = service.search_drafts(identity_simple, params={"facets": {"publication_status": ["published"]}})
    assert hits.total == 0

    # publish the record

    rec = service.publish(identity_simple, rec.id)
    assert rec.id is not None

    record = rec._record
    assert record.status == "published"
    assert rec.errors == []
    assert get_draft(record) is None
    assert not has_draft(record)

    service.config.draft_cls.index.refresh()
    service.config.record_cls.index.refresh()

    hits = service.search_drafts(identity_simple, params={"facets": {"publication_status": ["draft"]}})
    assert hits.total == 0

    hits = service.search(identity_simple)
    assert hits.total == 1

    items = list(hits.hits)
    assert len(items) == 1
    assert items[0]["result_component"]
    links = items[0]["links"]
    assert links["self"].endswith(f"/api/mocks/{rec.id}")
    assert links["self_html"].endswith(f"/mocks/{rec.id}")
    assert links["latest"].endswith(f"/api/mocks/{rec.id}/versions/latest")
    assert links["latest_html"].endswith(f"/mocks/{rec.id}/latest")
    assert links["draft"].endswith(f"/api/mocks/{rec.id}/draft")
    assert links["versions"].endswith(f"/api/mocks/{rec.id}/versions")
    assert links["files"].endswith(f"/api/mocks/{rec.id}/files")
    assert "record" not in links
    assert "publish" not in links

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
