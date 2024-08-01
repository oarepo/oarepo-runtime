import json


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
        "metadata_num": {"buckets": [], "label": "metadata/num.label"},
        "metadata_num_increased": {
            "buckets": [],
            "label": "metadata/num_increased.label",
        },
        "metadata_date": {
            "buckets": [],
            "interval": "1y",
            "label": "metadata/date.label",
        },
    }


def test_facets_with_system_fields(
    sample_data_system_field, client_with_credentials_admin, search_clear
):
    res = client_with_credentials_admin.get("/records2/")
    data = json.loads(res.data.decode("UTF-8"))
    assert data["aggregations"] == {
        "metadata_num": {
            "buckets": [
                {"doc_count": 1, "is_selected": False, "key": "1", "label": "1"},
                {"doc_count": 1, "is_selected": False, "key": "2", "label": "2"},
            ],
            "label": "metadata/num.label",
        },
        "metadata_num_increased": {
            "buckets": [
                {"doc_count": 1, "is_selected": False, "key": "2", "label": "2"},
                {"doc_count": 1, "is_selected": False, "key": "3", "label": "3"},
            ],
            "label": "metadata/num_increased.label",
        },
        "metadata_date": {
            "buckets": [],
            "interval": "1y",
            "label": "metadata/date.label",
        },
    }
