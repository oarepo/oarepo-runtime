from pathlib import Path

from records2.proxies import current_service
from records2.records.api import Records2Record

from oarepo_runtime.datastreams.fixtures import FixturesCallback, load_fixtures


def test_czech_search(app, custom_fields, search_clear, db, identity, location):
    load_fixtures(
        Path(__file__).parent / "czech_search_data", callback=FixturesCallback()
    )
    Records2Record.index.refresh()
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "záznam"})
        ]
        assert sorted(titles) == ["druhy", "prvni"]

        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "záznamy"})
        ]

        assert sorted(titles) == ["druhy", "prvni"]

        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "zaznam"})
        ]
        assert sorted(titles) == ["prvni"]  # does not match zaznamu

        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "neco"})
        ]
        assert sorted(titles) == ["treti"]


def test_implicit_lang_search(app, custom_fields, search_clear, db, identity, location):
    load_fixtures(
        Path(__file__).parent / "czech_search_data", callback=FixturesCallback()
    )
    Records2Record.index.refresh()
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "detail"})
        ]
        assert sorted(titles) == ["druhy", "treti"]

        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "maly"})
        ]
        assert sorted(titles) == ["druhy"]

        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "malý"})
        ]
        assert sorted(titles) == ["druhy"]

        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "Malý"})
        ]
        assert sorted(titles) == ["druhy"]

        titles = [
            rec["metadata"]["title"]
            for rec in current_service.search(identity, params={"q": "Maly"})
        ]
        assert sorted(titles) == ["druhy"]
