from pathlib import Path

from records2.proxies import current_service
from records2.records.api import Records2Record

from oarepo_runtime.datastreams import DataStreamCallback
from oarepo_runtime.datastreams.fixtures import FixturesCallback, load_fixtures


def test_czech_suggest(app, custom_fields, search_clear, db, identity, location):
    load_fixtures(Path(__file__).parent / "czech_data", callback=FixturesCallback())
    Records2Record.index.refresh()
    titles = []
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        for rec in current_service.search(identity, params={"suggest": "česk"}):
            titles.append(rec["metadata"]["title"])
        assert titles == [
            "Český záznam",
            "Cesky zaznam",
        ]
