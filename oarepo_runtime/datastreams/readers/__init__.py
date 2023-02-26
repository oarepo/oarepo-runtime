from abc import ABC, abstractmethod
import contextlib
from typing import Iterator
from ..datastreams import StreamEntry


class BaseReader(ABC):
    """Base reader."""

    def __init__(self, log, *, source=None, **kwargs):
        """Constructor.
        :param source: Data source (e.g. filepath, stream, ...)
        """
        self.source = source
        self._log = log

    @abstractmethod
    def __iter__(self) -> Iterator[StreamEntry]:
        """Yields data objects."""
        pass

    @contextlib.contextmanager
    def _open(self, mode="r"):
        if hasattr(self.source, "read"):
            yield self.source
        else:
            with open(self.source, mode) as f:
                yield f
