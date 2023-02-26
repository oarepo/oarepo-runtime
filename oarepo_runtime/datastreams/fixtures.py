from pathlib import Path
from oarepo_runtime.datastreams import DataStreamCatalogue, DataStream
import pkg_resources
import yaml
from flask import current_app
from invenio_records_resources.proxies import current_service_registry


def load_fixtures(fixture_dir=None):
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
    fixtures = set()
    if fixture_dir:
        catalogue = DataStreamCatalogue(Path(fixture_dir) / "catalogue.yaml")
        _load_fixtures_from_catalogue(catalogue, fixtures)
    for r in reversed(
        sorted(pkg_resources.iter_entry_points("oarepo.fixtures"), key=lambda r: r.name)
    ):
        pkg = r.load()
        pkg_fixture_dir = Path(pkg.__file__)
        if pkg_fixture_dir.is_file():
            pkg_fixture_dir = pkg_fixture_dir.parent
        catalogue = DataStreamCatalogue(pkg_fixture_dir / "catalogue.yaml")
        _load_fixtures_from_catalogue(catalogue, fixtures)


def _load_fixtures_from_catalogue(catalogue, fixtures):
    for stream_name in catalogue:
        if stream_name in fixtures:
            continue
        fixtures.add(stream_name)
        datastream: DataStream = catalogue.get_datastream(stream_name)
        for _entry in datastream.process():
            # intentionally pass
            pass


def dump_fixtures(fixture_dir, skip=None):
    if not skip:
        skip = tuple()
    fixture_dir = Path(fixture_dir)
    if not fixture_dir.exists():
        fixture_dir.mkdir(parents=True)
    catalogue_path = fixture_dir / "catalogue.yaml"
    catalogue_data = {}

    for service_id in current_service_registry._services:
        if service_id in skip:
            continue
        config_generator = (
            current_app.config.get(f"DATASTREAMS_CONFIG_GENERATOR_{service_id.upper()}")
            or current_app.config["DATASTREAMS_CONFIG_GENERATOR"]
        )
        for fixture_read_config, fixture_write_config in config_generator(service_id):
            catalogue = DataStreamCatalogue(catalogue_path, fixture_write_config)
            catalogue_data.update(fixture_read_config)
            for stream_name in catalogue:
                datastream: DataStream = catalogue.get_datastream(stream_name)
                for _entry in datastream.process():
                    # intentionally pass
                    pass
    with open(catalogue_path, "w") as f:
        yaml.dump(catalogue_data, f)


def default_config_generator(service_id):
    return [
        (
            {
                # read
                service_id: [{"service": service_id}, {"source": f"{service_id}.yaml"}]
            },
            {
                # write
                service_id: [
                    {"reader": "service", "service": service_id},
                    {"writer": "yaml", "target": f"{service_id}.yaml"},
                ]
            },
        )
    ]
