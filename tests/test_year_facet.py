from pathlib import Path
from pprint import pprint

from records2.proxies import current_service
from records2.records.api import Records2Record

from oarepo_runtime.datastreams.fixtures import FixturesCallback, load_fixtures


def test_year_facet(app, custom_fields, search_clear, db, identity, location):
    import_result = FixturesCallback()
    load_fixtures(Path(__file__).parent / "year_facet_data", callback=import_result)
    assert import_result.failed_entries_count == 0

    Records2Record.index.refresh()

    with app.test_request_context():
        aggregations = current_service.search(identity, params={}).aggregations
        assert "metadata_date" in aggregations
        assert {
            "doc_count": 1,
            "end": "1909",
            "interval": "10y",
            "key": "-2208988800000",
            "key_as_string": "1900",
            "start": "1900",
        } in aggregations["metadata_date"]["buckets"]
        assert {
            "doc_count": 0,
            "end": "1919",
            "interval": "10y",
            "key": "-1893456000000",
            "key_as_string": "1910",
            "start": "1910",
        } in aggregations["metadata_date"]["buckets"]
        assert {
            "doc_count": 3,
            "end": "2029",
            "interval": "10y",
            "key": "1577836800000",
            "key_as_string": "2020",
            "start": "2020",
        } in aggregations["metadata_date"]["buckets"]

    with app.test_request_context():
        aggregations = current_service.search(
            identity, params={"facets": {"metadata_date": ["2020/2025"]}}
        ).aggregations
        pprint(aggregations)
        assert {
            "doc_count": 2,
            "end": "2020",
            "interval": "1y",
            "key": "1577836800000",
            "key_as_string": "2020",
            "start": "2020",
        } in aggregations["metadata_date"]["buckets"]
        assert {
            "key_as_string": "2024",
            "key": "1704067200000",
            "doc_count": 1,
            "interval": "1y",
            "start": "2024",
            "end": "2024",
        } in aggregations["metadata_date"]["buckets"]
        assert len(aggregations["metadata_date"]["buckets"]) == 5

    with app.test_request_context():
        aggregations = current_service.search(
            identity, params={"facets": {"metadata_date": ["2020/2020"]}}
        ).aggregations
        assert {
            "doc_count": 2,
            "end": "2020",
            "interval": "1y",
            "key": "1577836800000",
            "key_as_string": "2020",
            "start": "2020",
        } in aggregations["metadata_date"]["buckets"]
        assert len(aggregations["metadata_date"]["buckets"]) == 1
