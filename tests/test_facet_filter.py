import json

from flask import session
from flask_babel import get_locale


def test_multilang_facets(sample_data, client_with_credentials_curator, search_clear):
    res = client_with_credentials_curator.get("/records2/")
    data = json.loads(res.data.decode("UTF-8"))
    aggs = data["aggregations"]

    assert "metadata_subjects" in aggs
    print(aggs["metadata_subjects"])
    assert get_locale().language == "en"

    assert aggs["metadata_subjects"] == {
        "buckets": [
            {"doc_count": 1, "is_selected": False, "key": "jej", "label": "jej"}
        ],
        "label": "metadata/subjects.label",
    }


def test_facets_with_role_facets(
    sample_data, client_with_credentials_curator, search_clear
):
    res = client_with_credentials_curator.get("/records2/")
    data = json.loads(res.data.decode("UTF-8"))
    aggs = data["aggregations"]

    assert "metadata_title" in aggs

    assert aggs["metadata_title"] == {
        "buckets": [
            {
                "doc_count": 1,
                "is_selected": False,
                "key": "record 1",
                "label": "record 1",
            },
            {
                "doc_count": 1,
                "is_selected": False,
                "key": "record 2",
                "label": "record 2",
            },
        ],
        "label": "metadata/title.label",
    }


def test_facets_not_existing_role(
    sample_data, client_with_credentials_admin, search_clear
):
    res = client_with_credentials_admin.get("/records2/")
    data = json.loads(res.data.decode("UTF-8"))

    assert data["aggregations"] == {
        "metadata_date": {
            "buckets": [],
            "label": "metadata/date.label",
            "interval": "1y",
        },
        "metadata_num": {"buckets": [], "label": "metadata/num.label"},
        "metadata_num_increased": {
            "buckets": [],
            "label": "metadata/num_increased.label",
        },
        "metadata_subjects_cs": {
            "buckets": [
                {"key": "jupii", "doc_count": 1, "label": "jupii", "is_selected": False}
            ],
            "label": "metadata/subjects.label",
        },
        "metadata_subjects_en": {
            "buckets": [
                {"key": "jej", "doc_count": 1, "label": "jej", "is_selected": False}
            ],
            "label": "metadata/subjects.label",
        },
        "metadata_subjects": {
            "buckets": [
                {"key": "jej", "doc_count": 1, "label": "jej", "is_selected": False}
            ],
            "label": "metadata/subjects.label",
        },
    }


def test_facets_with_system_fields(
    sample_data_system_field, client_with_credentials_admin, search_clear
):
    res = client_with_credentials_admin.get("/records2/")
    data = json.loads(res.data.decode("UTF-8"))

    assert data["aggregations"] == {
        "metadata_date": {
            "buckets": [],
            "label": "metadata/date.label",
            "interval": "1y",
        },
        "metadata_num": {
            "buckets": [
                {"key": "1", "doc_count": 1, "label": "1", "is_selected": False},
                {"key": "2", "doc_count": 1, "label": "2", "is_selected": False},
            ],
            "label": "metadata/num.label",
        },
        "metadata_num_increased": {
            "buckets": [
                {"key": "2", "doc_count": 1, "label": "2", "is_selected": False},
                {"key": "3", "doc_count": 1, "label": "3", "is_selected": False},
            ],
            "label": "metadata/num_increased.label",
        },
        "metadata_subjects_cs": {"buckets": [], "label": "metadata/subjects.label"},
        "metadata_subjects_en": {"buckets": [], "label": "metadata/subjects.label"},
        "metadata_subjects": {"buckets": [], "label": "metadata/subjects.label"},
    }
