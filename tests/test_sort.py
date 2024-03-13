from pathlib import Path

from oarepo_runtime.datastreams.fixtures import FixturesCallback, load_fixtures
from records2.proxies import current_service
from records2.records.api import Records2Record


def test_czech_sort(app, custom_fields, search_clear, db, identity, location):
    load_fixtures(Path(__file__).parent / "czech_data", callback=FixturesCallback())
    Records2Record.index.refresh()
    titles = []
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        for rec in current_service.search(identity, params={"sort": "title"}):
            titles.append(rec["metadata"]["title"])
        assert titles == [
            "Cesky zaznam",
            "Český záznam",
            "Další záznam",
        ]
