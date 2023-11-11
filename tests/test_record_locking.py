import threading
from pathlib import Path

import pytest
from records2.proxies import current_service
from records2.records.api import Records2Record

from oarepo_runtime.datastreams import DataStreamCallback
from oarepo_runtime.datastreams.fixtures import load_fixtures
from oarepo_runtime.records import select_record_for_update


@pytest.mark.xfail(reason="sqlite3 does not support locking")
def test_lock_record(db, app, search_clear, location, identity):
    load_fixtures(Path(__file__).parent / "czech_data", callback=DataStreamCallback())
    Records2Record.index.refresh()
    first_record = list(current_service.search(identity))[0]

    first_record_id = first_record["id"]

    rec = select_record_for_update(Records2Record, first_record_id)
    assert rec["metadata"]["title"] == first_record["metadata"]["title"]
    assert rec["id"] == first_record_id

    other_thread_has_access = False
    other_thread_failed = False

    db.session.expunge_all()

    def other_thread():
        nonlocal other_thread_has_access, other_thread_failed
        with app.test_request_context():
            try:
                select_record_for_update(Records2Record, first_record_id)
                other_thread_has_access = True
            except Exception:
                other_thread_failed = True
                import traceback

                traceback.print_exc()

    thread = threading.Thread(target=other_thread)
    thread.start()
    thread.join(timeout=5)

    assert other_thread_has_access is False
    assert other_thread_failed is False
