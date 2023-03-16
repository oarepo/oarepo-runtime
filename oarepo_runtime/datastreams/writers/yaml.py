import yaml

from oarepo_runtime.datastreams import StreamEntry

from . import BaseWriter


class YamlWriter(BaseWriter):
    """Writes the entries to a YAML file."""

    def __init__(self, *, target, base_path=None, **kwargs):
        """Constructor.
        :param file_or_path: path of the output file.
        """
        super().__init__(**kwargs)
        if hasattr(target, "read"):
            # opened file
            self._file = target
            self._stream = target
        else:
            self._stream = None
            if base_path:
                self._file = base_path.joinpath(target)
            else:
                self._file = target
        self._started = False

    def write(self, entry: StreamEntry, *args, **kwargs):
        """Writes the input stream entry using a given service."""
        if not self._started:
            self._started = True
            if not self._stream:
                self._stream = open(self._file, "w")
        else:
            self._stream.write("---\n")
        yaml.safe_dump(entry.entry, self._stream)
        return entry

    def delete(self, stream_entry: StreamEntry):
        """noop"""

    def finish(self):
        """Finalizes writing"""
        if not hasattr(self._file, "read") and self._stream:
            self._stream.close()
