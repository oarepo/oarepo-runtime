import json
from typing import Iterator

from . import BaseReader, StreamEntry


class JSONReader(BaseReader):
    """JSON Lines data iterator that loads records from JSON Lines files."""

    def __iter__(self) -> Iterator[StreamEntry]:
        """Iterate over records."""
        with self._open() as fp:
            data = json.load(fp)
            assert isinstance(data, list)
            for d in data:
                yield StreamEntry(d)


class JSONLinesReader(BaseReader):
    """JSON Lines data iterator that loads records from JSON Lines files."""

    def __iter__(self) -> Iterator[StreamEntry]:
        """Iterate over records."""
        with self._open() as fp:
            for line in fp:
                yield StreamEntry(json.loads(line))
