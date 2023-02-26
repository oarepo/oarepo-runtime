from pathlib import Path
from . import DataStream
from .errors import DataStreamCatalogueError
from flask import current_app
from werkzeug.utils import import_string
from logging import getLogger
import yaml


class DataStreamCatalogue:
    def __init__(self, catalogue, content=None) -> None:
        """
        Catalogue of data streams. The catalogue contains a dict of:
        stream_name: stream_definition, where stream definition is an array of:

        - reader: reader_class
          <rest of parameters go to reader constructor>
        - transformer: transformer_class
          <rest of parameters go to transformer constructor>
        - writer: writer_class
          <rest of parameters go to writer constructor>

        If reader class is not passed and _source_ is, then the reader class will be taken from the
        DATASTREAMS_READERS_BY_EXTENSION config variable - map from file extension to reader class.

        If 'service' is passed, service writer will be used with this service

        Transformer class must always be passed.
        """
        self._catalogue_path = Path(catalogue)
        if content:
            self._catalogue = content
        else:
            with open(catalogue) as f:
                self._catalogue = yaml.safe_load(f)

    @property
    def path(self):
        return self._catalogue_path

    @property
    def directory(self):
        return self._catalogue_path.parent

    def get_datastreams(self):
        for stream_name in self._catalogue:
            yield self.get_datastream(stream_name)

    def __iter__(self):
        return iter(self._catalogue)

    def get_datastream(self, stream_name):
        stream_definition = self._catalogue[stream_name]
        readers = []
        transformers = []
        writers = []
        log = getLogger(f"datastreams.{stream_name}")
        for entry in stream_definition:
            entry = {**entry}
            try:
                if "reader" in entry:
                    readers.append(
                        self._get_instance(
                            log,
                            "DATASTREAMS_READERS",
                            entry.pop("reader"),
                            entry,
                        )
                    )
                elif "transformer" in entry:
                    transformers.append(
                        self._get_instance(
                            log,
                            "DATASTREAMS_TRANSFORMERS",
                            entry.pop("transformer"),
                            entry,
                        )
                    )
                elif "writer" in entry:
                    writers.append(
                        self._get_instance(
                            log,
                            "DATASTREAMS_WRITERS",
                            entry.pop("writer"),
                            entry,
                        )
                    )
                elif "source" in entry:
                    readers.append(self._get_reader(log, entry))
                elif "service" in entry:
                    writers.append(self._get_service_writer(log, entry))
                else:
                    raise DataStreamCatalogueError(
                        "Can not decide what this record is - reader, transformer or service?"
                    )
            except DataStreamCatalogueError as e:
                e.entry = entry
                e.stream_name = stream_name
                raise e
        ds = DataStream(readers=readers, transformers=transformers, writers=writers)
        return ds

    def _get_reader(self, log, entry):
        try:
            source = Path(entry["source"])
            ext = source.suffix[1:]
            reader_class = (
                current_app.config["DATASTREAMS_READERS_BY_EXTENSION"].get(ext)
                or current_app.config["DEFAULT_DATASTREAMS_READERS_BY_EXTENSION"][ext]
            )
        except KeyError:
            raise DataStreamCatalogueError(
                f"Do not have loader for file {source} - extension {ext} not defined in DATASTREAMS_READERS_BY_EXTENSION config"
            )
        entry["source"] = self._catalogue_path.parent.joinpath(entry["source"])
        return self._get_instance(log, "DATASTREAMS_READERS", reader_class, entry)

    def _get_service_writer(self, log, entry):
        from .writers.service import ServiceWriter

        return self._get_instance(log, None, ServiceWriter, entry)

    def _get_instance(self, log, config_section, clz, entry):
        if isinstance(clz, str):
            try:
                clz = (
                    current_app.config[config_section].get(clz)
                    or current_app.config[f"DEFAULT_{config_section}"][clz]
                )
            except KeyError:
                raise DataStreamCatalogueError(
                    f"Do not have implementation - '{clz}' not defined in {config_section} config"
                )
            if isinstance(clz, str):
                clz = import_string(clz)
        return clz(log=log, catalogue=self, **entry)
