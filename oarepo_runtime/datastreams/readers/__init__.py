import contextlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from ..datastreams import StreamEntry


class BaseReader(ABC):
    """Base reader."""

    def __init__(self, *, source=None, base_path=None, **kwargs):
        """Constructor.
        :param source: Data source (e.g. filepath, stream, ...)
        """
        if not source or hasattr(source, "read") or not base_path:
            self.source = source
        else:
            self.source = Path(base_path).joinpath(source)

    @abstractmethod
    def __iter__(self) -> Iterator[StreamEntry]:
        """Yields data objects."""

    @contextlib.contextmanager
    def _open(self, mode="r"):
        if hasattr(self.source, "read"):
            yield self.source
        else:
            with open(self.source, mode) as f:
                yield f
