from pathlib import Path

import yaml
from flask import current_app
from invenio_access.permissions import system_identity

from .config import get_instance
from .datastreams import DataStream
from .errors import DataStreamCatalogueError


class DataStreamCatalogue:
    def __init__(self, catalogue, content=None, identity=system_identity) -> None:
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
        self.identity = identity

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
        for entry in stream_definition:
            entry = {**entry}
            try:
                if "reader" in entry:
                    readers.append(
                        get_instance(
                            "DATASTREAMS_READERS",
                            "reader",
                            entry,
                            base_path=self.directory,
                            identity=self.identity,
                        )
                    )
                elif "transformer" in entry:
                    transformers.append(
                        get_instance(
                            "DATASTREAMS_TRANSFORMERS",
                            "transformer",
                            entry,
                            base_path=self.directory,
                            identity=self.identity,
                        )
                    )
                elif "writer" in entry:
                    writers.append(
                        get_instance(
                            "DATASTREAMS_WRITERS",
                            "writer",
                            entry,
                            base_path=self.directory,
                            identity=self.identity,
                        )
                    )
                elif "source" in entry:
                    readers.append(self.get_reader(entry))
                elif "service" in entry:
                    writers.append(self.get_service_writer(entry))
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

    def get_reader(self, entry):
        entry = {**entry}
        if not entry.get("reader"):
            try:
                source = Path(entry["source"])
                ext = source.suffix[1:]
                reader_class = (
                    current_app.config["DATASTREAMS_READERS_BY_EXTENSION"].get(ext)
                    or current_app.config["DEFAULT_DATASTREAMS_READERS_BY_EXTENSION"][
                        ext
                    ]
                )
                entry["reader"] = reader_class
            except KeyError:
                raise DataStreamCatalogueError(
                    f"Do not have loader for file {source} - extension {ext} not defined in DATASTREAMS_READERS_BY_EXTENSION config"
                )
        return get_instance(
            "DATASTREAMS_READERS",
            "reader",
            entry,
            base_path=self.directory,
            identity=self.identity,
        )

    def get_service_writer(self, entry):
        from .writers.service import ServiceWriter

        return get_instance(
            None, ServiceWriter, entry, base_path=self.directory, identity=self.identity
        )
