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
    assert "aggregations" not in data
