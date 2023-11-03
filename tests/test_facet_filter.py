import json


def test_facets_with_role_facets(
    sample_data, client_with_credentials_curator, search_clear
):
    res = client_with_credentials_curator.get("/records2/")
    data = json.loads(res.data.decode("UTF-8"))
    aggs = data["aggregations"]

    assert len(aggs) == 5
    assert all(
        key in aggs
        for key in ["_schema", "created", "_id", "updated", "metadata_title"]
    )


def test_facets_not_existing_role(
    sample_data, client_with_credentials_admin, search_clear
):
    res = client_with_credentials_admin.get("/records2/")
    data = json.loads(res.data.decode("UTF-8"))
    aggs = data["aggregations"]

    assert len(aggs) == 4
    assert all(key in aggs for key in ["_schema", "created", "_id", "updated"])
