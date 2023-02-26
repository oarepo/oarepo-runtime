import yaml

from . import BaseReader, StreamEntry


class YamlReader(BaseReader):
    """YAML data iterator that loads records from YAML files."""

    def __iter__(self):
        """Iterate over records."""
        with self._open() as fp:
            for entry in yaml.safe_load_all(fp):
                yield StreamEntry(entry)
