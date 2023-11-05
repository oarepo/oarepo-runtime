from io import StringIO
from pathlib import Path

import yaml

from oarepo_runtime.datastreams import BaseWriter, StreamBatch


class YamlWriter(BaseWriter):
    """Writes the entries to a YAML file."""

    def __init__(self, *, target, base_path=None, **kwargs):
        """Constructor.
        :param file_or_path: path of the output file.
        """
        super().__init__(**kwargs)
        if hasattr(target, "write"):
            # opened file
            self._file = target
            self._stream = target
        else:
            if base_path:
                self._file = Path(base_path).joinpath(target)
            else:
                self._file = target
            self._stream = open(self._file, "w")

        self._started = False

    def write(self, batch: StreamBatch):
        """Writes the input stream entry using a given service."""

        for entry in batch.entries:
            if not entry.ok:
                continue

            self._write_entry_separator()

            try:
                io = StringIO()
                yaml.safe_dump(entry.entry, io)
                self._stream.write(io.getvalue())
            except Exception as e:
                entry.errors.append(e)

        return batch

    def _write_entry_separator(self):
        if not self._started:
            self._started = True
        else:
            self._stream.write("---\n")

    def finish(self):
        """Finalizes writing"""
        self._stream.close()
