import logging
import re
from pathlib import Path

import pkg_resources
import yaml
from celery import shared_task
from flask import current_app
from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime.datastreams import (
    DataStreamCatalogue,
    StreamBatch,
    SynchronousDataStream,
)
from oarepo_runtime.datastreams.types import StatsKeepingDataStreamCallback

log = logging.getLogger("fixtures")


class FixturesCallback(StatsKeepingDataStreamCallback):
    def fixture_started(self, fixture_name):
        pass

    def fixture_finished(self, fixture_name):
        pass


def load_fixtures(
    fixture_dir=None,
    include=None,
    exclude=None,
    system_fixtures=True,
    callback: FixturesCallback = None,
    batch_size=100,
    datastreams_impl=SynchronousDataStream,
    identity=system_identity,
):
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

    if fixture_dir:
        catalogue = DataStreamCatalogue(Path(fixture_dir) / "catalogue.yaml")
        _load_fixtures_from_catalogue(
            catalogue,
            fixtures,
            include,
            exclude,
            callback,
            batch_size=batch_size,
            datastreams_impl=datastreams_impl,
            identity=identity,
        )

    if system_fixtures:

        def get_priority(name):
            match = re.match(r"(\d+)-", name)
            if match:
                return -int(match.group(1))
            return 0

        entry_points = list(
            (get_priority(r.name), r.name, r)
            for r in pkg_resources.iter_entry_points("oarepo.fixtures")
        )
        entry_points.sort(key=lambda x: x[:2])
        for r in entry_points:
            pkg = r[2].load()
            pkg_fixture_dir = Path(pkg.__file__)
            if pkg_fixture_dir.is_file():
                pkg_fixture_dir = pkg_fixture_dir.parent
            catalogue = DataStreamCatalogue(pkg_fixture_dir / "catalogue.yaml")
            _load_fixtures_from_catalogue(
                catalogue,
                fixtures,
                include,
                exclude,
                callback,
                batch_size=batch_size,
                datastreams_impl=datastreams_impl,
                identity=identity,
            )


def _load_fixtures_from_catalogue(
    catalogue,
    fixtures,
    include,
    exclude,
    callback,
    batch_size,
    datastreams_impl,
    identity=system_identity,
):
    for catalogue_datastream in catalogue.get_datastreams():
        if catalogue_datastream.stream_name in fixtures:
            continue
        if include and not any(
            x.match(catalogue_datastream.stream_name) for x in include
        ):
            continue
        if any(x.match(catalogue_datastream.stream_name) for x in exclude):
            continue

        fixtures.add(catalogue_datastream.stream_name)

        if hasattr(callback, "fixture_started"):
            callback.fixture_started(catalogue_datastream.stream_name)
        datastream = datastreams_impl(
            readers=catalogue_datastream.readers,
            writers=catalogue_datastream.writers,
            transformers=catalogue_datastream.transformers,
            callback=callback,
            batch_size=batch_size,
        )
        datastream.process(identity=identity)
        if hasattr(callback, "fixture_finished"):
            callback.fixture_finished(catalogue_datastream.stream_name)


def dump_fixtures(
    fixture_dir,
    include=None,
    exclude=None,
    use_files=False,
    callback: FixturesCallback = None,
    datastream_impl=SynchronousDataStream,
    batch_size=1,
):
    include = [re.compile(x) for x in (include or [])]
    exclude = [
        re.compile(x)
        for x in (exclude or current_app.config.get("DATASTREAMS_EXCLUDES", []))
    ]
    fixture_dir = Path(fixture_dir)
    if not fixture_dir.exists():
        fixture_dir.mkdir(parents=True)
    catalogue_path = fixture_dir / "catalogue.yaml"
    catalogue_data = {}

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

            catalogue_data[fixture_name] = fixture_read_config

            catalogue = DataStreamCatalogue(
                catalogue_path, {fixture_name: fixture_write_config}
            )

            for stream_name in catalogue:
                catalogue_datastream = catalogue.get_datastream(stream_name)
                if hasattr(callback, "fixture_started"):
                    callback.fixture_started(stream_name)
                datastream = datastream_impl(
                    readers=catalogue_datastream.readers,
                    writers=catalogue_datastream.writers,
                    transformers=catalogue_datastream.transformers,
                    callback=callback,
                    batch_size=batch_size,
                )
                datastream.process()
                if hasattr(callback, "fixture_finished"):
                    callback.fixture_finished(stream_name)

    with open(catalogue_path, "w") as f:
        yaml.dump(catalogue_data, f)


def default_config_generator(service_id, use_files=False):
    writers = [
        {"writer": "yaml", "target": f"{service_id}.yaml"},
    ]
    if use_files:
        writers.append(
            {"writer": "attachments_file", "target": f"files"},
        )

    yield service_id, [
        # load
        {"writer": "service", "service": service_id},
        {"writer": "attachments_service", "service": service_id},
        {"source": f"{service_id}.yaml"},
    ], [
        # dump
        {"reader": "service", "service": service_id, "load_files": use_files},
        *writers,
    ]


@shared_task
def fixtures_asynchronous_callback(*args, callback, **kwargs):
    try:
        if "batch" in kwargs:
            batch = StreamBatch.from_json(kwargs["batch"])
            log.info(
                "Fixtures progress: %s in batch.seq=%s, batch.last=%s",
                callback,
                batch.seq,
                batch.last,
            )
        else:
            batch = None
            log.info(f"Fixtures progress: %s", callback)

        if "error" in callback:
            log.error(
                f"Error in loading fixtures: %s\n%s\n%s",
                callback,
                "\n".join(args),
                "\n".join(f"{kwarg}: {value}" for kwarg, value in kwargs.items()),
            )

        if batch:
            if batch.errors:
                log.error(
                    "Batch errors: batch %s:\n%s",
                    batch.seq,
                    "\n".join(str(x) for x in batch.errors),
                )

            for entry in batch.entries:
                if entry.errors:
                    log.error(
                        f"Errors in entry %s of batch %s:\npayload %s\n",
                        entry.seq,
                        batch.seq,
                        entry.entry,
                        "\n".join(str(x) for x in entry.errors),
                    )
    except Exception as e:
        print(f"Error in fixtures callback: {callback=}, {args=}, {kwargs=}")
