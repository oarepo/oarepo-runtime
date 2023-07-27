import yaml

from . import BaseReader, StreamEntry
from .attachments import AttachmentsReaderMixin


class YamlReader(AttachmentsReaderMixin, BaseReader):
    """YAML data iterator that loads records from YAML files."""

    def iter_entries(self):
        """Iterate over records."""
        with self._open() as fp:
            for entry in yaml.safe_load_all(fp):
                yield StreamEntry(entry)
