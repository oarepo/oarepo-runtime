from pathlib import Path

from oarepo_runtime.datastreams import StreamEntry
from . import BaseWriter
import yaml


class YamlWriter(BaseWriter):
    """Writes the entries to a YAML file."""

    def __init__(self, log, *, target, catalogue=None, **kwargs):
        """Constructor.
        :param file_or_path: path of the output file.
        """
        super().__init__(log, **kwargs)
        if hasattr(target, "read"):
            # opened file
            self._file = target
            self._stream = target
        else:
            if catalogue:
                self._file = catalogue.directory.joinpath(target)
            else:
                self._file = target
            self._stream = open(self._file, "w")
        self._started = False

    def write(self, entry: StreamEntry, *args, **kwargs):
        """Writes the input stream entry using a given service."""
        if self._started:
            self._stream.write("---\n")
        else:
            self._started = True
        yaml.safe_dump(entry.entry, self._stream)
        return entry

    def finish(self):
        """Finalizes writing"""
        if isinstance(self._file, str):
            self._stream.close()
