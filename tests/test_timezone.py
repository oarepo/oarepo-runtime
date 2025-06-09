from datetime import datetime

import pytest


@pytest.fixture()
def record_service():
    from thesis.proxies import current_service

    return current_service


def test_ui_serialization(
    db,
    logged_client,
    record_factory,
    location,
    search_clear,
    users,
):
    BASE_URL = "/thesis/"
    record = record_factory(users[0].identity)

    users[3].refresh()
    african_client = logged_client(users[3])
    u = african_client.get(
        f"{BASE_URL}{record['id']}",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    ).json["created"]

    users[4].refresh()
    mexican_client = logged_client(users[4])
    m = mexican_client.get(
        f"{BASE_URL}{record['id']}",
        headers={"Accept": "application/vnd.inveniordm.v1+json"},
    ).json["created"]

    datetime_format = "%b %d, %Y, %I:%M:%S %p"
    dt1 = datetime.strptime(u.replace("\u202f", " "), datetime_format)
    dt2 = datetime.strptime(m.replace("\u202f", " "), datetime_format)

    time_diff = (dt1 - dt2).total_seconds() / 3600

    assert time_diff == 6
