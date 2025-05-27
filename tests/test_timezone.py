from thesis.records.api import ThesisDraft, ThesisRecord
import pytest
from datetime import datetime


@pytest.fixture()
def record_service():
    from thesis.proxies import current_service

    return current_service

def test_ui_serialization(db, users, logged_client, record_factory, location, search_clear):
    BASE_URL = "/thesis/"
    record = record_factory(users[0].identity)
    african_client = logged_client(users[3])
    mexican_client = logged_client(users[4])
    ThesisRecord.index.refresh()
    u = african_client.get(f"{BASE_URL}{record['id']}", headers={"Accept": "application/vnd.inveniordm.v1+json"}).json["created"]
    m = mexican_client.get(f"{BASE_URL}{record['id']}", headers={"Accept": "application/vnd.inveniordm.v1+json"}).json["created"]

    datetime_format = "%B %d, %Y, %I:%M:%S %p"
    dt1 = datetime.strptime(u, datetime_format)
    dt2 = datetime.strptime(m, datetime_format)

    time_diff = (dt1 - dt2).total_seconds() / 3600

    assert time_diff == 6