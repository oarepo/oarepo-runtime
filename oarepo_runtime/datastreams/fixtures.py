import dataclasses
import re
from pathlib import Path
from typing import Dict

import pkg_resources
import yaml
from flask import current_app
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime.datastreams import DataStream, DataStreamCatalogue, DataStreamResult


@dataclasses.dataclass
class FixturesResult:
    ok_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    results: Dict[str, DataStreamResult] = dataclasses.field(default_factory=dict)

    @property
    def failed_entries(self):
        ret = []
        r: DataStreamResult
        for r in self.results:
            ret.extend(r.failed_entries or [])
        return ret

    def add(self, fixture_name, result: DataStreamResult):
        self.ok_count += result.ok_count
        self.failed_count += result.failed_count
        self.skipped_count += result.skipped_count
        self.results[fixture_name] = result


def load_fixtures(
    fixture_dir=None, include=None, exclude=None, system_fixtures=True
) -> FixturesResult:
    """
    Loads fixtures. If fixture dir is set, fixtures are loaded from that directory first.
    The directory must contain a catalogue.yaml file containing datastreams to load the
    fixtures. The format of the catalogue is described in the 'catalogue.py' file.

    Then fixture loading continues with fixtures defined in `oarepo.fixtures` entrypoint.
    The entry points are sorted and those with the greatest `name` are processed first -
    so the recommendation is to call the entry points 0000-something, where 0000 is a 4-digit
    number. oarepo entry points always have this number set to 1000.

    If a datastream is loaded from one fixture, it will not be loaded again from another fixture.
    If you want to override the default fixtures, just register your own with a key bigger than 1000.
    """
    include = [re.compile(x) for x in (include or [])]
    exclude = [re.compile(x) for x in (exclude or [])]
    fixtures = set()
    result = FixturesResult()

    if fixture_dir:
        catalogue = DataStreamCatalogue(Path(fixture_dir) / "catalogue.yaml")
        _load_fixtures_from_catalogue(catalogue, fixtures, include, exclude, result)
    if system_fixtures:
        for r in reversed(
            sorted(
                pkg_resources.iter_entry_points("oarepo.fixtures"), key=lambda r: r.name
            )
        ):
            pkg = r.load()
            pkg_fixture_dir = Path(pkg.__file__)
            if pkg_fixture_dir.is_file():
                pkg_fixture_dir = pkg_fixture_dir.parent
            catalogue = DataStreamCatalogue(pkg_fixture_dir / "catalogue.yaml")
            _load_fixtures_from_catalogue(catalogue, fixtures, include, exclude, result)
    return result


def _load_fixtures_from_catalogue(
    catalogue, fixtures, include, exclude, result: FixturesResult
):
    for stream_name in catalogue:
        if stream_name in fixtures:
            continue
        if include and not any(x.match(stream_name) for x in include):
            continue
        if any(x.match(stream_name) for x in exclude):
            continue
        fixtures.add(stream_name)
        datastream: DataStream = catalogue.get_datastream(stream_name)
        result.add(stream_name, datastream.process())


def dump_fixtures(fixture_dir, include=None, exclude=None, use_files=False) -> FixturesResult:
    include = [re.compile(x) for x in (include or [])]
    exclude = [
        re.compile(x)
        for x in (
            exclude
            or current_app.config.get(
                "DATASTREAMS_EXCLUDES",
                current_app.config["DEFAULT_DATASTREAMS_EXCLUDES"],
            )
        )
    ]
    fixture_dir = Path(fixture_dir)
    if not fixture_dir.exists():
        fixture_dir.mkdir(parents=True)
    catalogue_path = fixture_dir / "catalogue.yaml"
    catalogue_data = {}

    result = FixturesResult()

    for service_id in current_service_registry._services:
        config_generator = (
            current_app.config.get(f"DATASTREAMS_CONFIG_GENERATOR_{service_id.upper()}")
            or current_app.config["DATASTREAMS_CONFIG_GENERATOR"]
        )
        service = current_service_registry.get(service_id)
        if not hasattr(service, "scan"):
            continue
        for fixture_name, fixture_read_config, fixture_write_config in config_generator(
            service_id, use_files=use_files
        ):
            if include and not any(x.match(fixture_name) for x in include):
                continue
            if any(x.match(fixture_name) for x in exclude):
                continue

            catalogue = DataStreamCatalogue(
                catalogue_path, {fixture_name: fixture_write_config}
            )
            for stream_name in catalogue:
                datastream: DataStream = catalogue.get_datastream(stream_name)
                datastream_result = datastream.process()
                if datastream_result.ok_count:
                    catalogue_data[fixture_name] = fixture_read_config
                result.add(stream_name, datastream_result)

    with open(catalogue_path, "w") as f:
        yaml.dump(catalogue_data, f)

    return result


def default_config_generator(service_id, use_files=False):
    writers = [
        {"writer": "yaml", "target": f"{service_id}.yaml"},
    ]
    if use_files:
        writers.append(
            {"writer": "attachments", "target": f"files"},
        )

    yield service_id, [
        # load
        {"service": service_id},
        {"source": f"{service_id}.yaml"},
    ], [
        # dump
        {"reader": "service", "service": service_id, "load_files": use_files},
        *writers
    ]
