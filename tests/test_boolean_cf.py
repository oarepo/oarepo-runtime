from pathlib import Path

from oarepo_runtime.datastreams import StreamBatch
from oarepo_runtime.datastreams.fixtures import load_fixtures, FixturesCallback
from records2.proxies import current_service
from records2.records.api import Records2Record


class StrictCallback(FixturesCallback):
    def batch_finished(self, batch: StreamBatch):
        super().batch_finished(batch)
        if batch.errors:
            raise Exception(f"Batch {batch} failed: {batch.errors}")
        if batch.failed_entries:
            raise Exception(f"Batch {batch} failed: {batch.failed_entries}")


def test_boolean_cf(app, custom_fields, search_clear, db, identity, location):
    load_fixtures(Path(__file__).parent / "cf_data", callback=StrictCallback())
    Records2Record.index.refresh()
    boolean_cf = {}
    with app.test_request_context(headers=[("Accept-Language", "cs")]):
        for rec in current_service.search(identity, params={"sort": "newest"}):
            boolean_cf[rec['metadata']['title']] = rec["custom_fields"]["test"]
    assert boolean_cf == {
        'Další záznam': True,
        'Český záznam': False,
        'Cesky zaznam': True
    }
