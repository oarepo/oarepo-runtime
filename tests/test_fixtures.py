import tempfile
from pathlib import Path

import yaml

from oarepo_runtime.datastreams import DataStreamCallback
from oarepo_runtime.datastreams.fixtures import dump_fixtures, load_fixtures
from records2.proxies import current_service
from records2.records.api import Records2Record


def read_yaml(fp):
    with open(fp) as f:
        ret = list(yaml.safe_load_all(f))
        if len(ret) == 1:
            return ret[0]
        return ret


def test_pkg_fixtures(db, app, identity, search_clear, location):
    load_fixtures(callback=DataStreamCallback())

    Records2Record.index.refresh()
    titles = set()
    for rec in current_service.scan(identity):
        titles.add(rec["metadata"]["title"])
    assert titles == {"pkg record 1", "pkg record 2"}


def test_extra_fixtures(db, app, identity, search_clear, location):
    load_fixtures(Path(__file__).parent / "data", callback=DataStreamCallback())
    Records2Record.index.refresh()
    titles = set()
    for rec in current_service.scan(identity):
        titles.add(rec["metadata"]["title"])
    assert titles == {"record 1", "record 2"}


def test_load_dump(db, app, identity, search_clear, location):
    load_fixtures(callback=DataStreamCallback())
    Records2Record.index.refresh()
    with tempfile.TemporaryDirectory() as fixture_dir:
        dump_fixtures(fixture_dir, callback=DataStreamCallback())

        fixture_dir = Path(fixture_dir)

        assert read_yaml(fixture_dir / "catalogue.yaml")["records2"] == [
            {"service": "records2", "writer": "service"},
            {"service": "records2", "writer": "attachments_service"},
            {"source": "records2.yaml"},
        ]
        assert set(
            x["metadata"]["title"] for x in read_yaml(fixture_dir / "records2.yaml")
        ) == {"pkg record 1", "pkg record 2"}
