import contextlib
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterator

from ..datastreams import StreamEntry


class BaseReader(ABC):
    """Base reader."""
    base_path: Path

    def __init__(self, *, source=None, base_path=None, **kwargs):
        """Constructor.
        :param source: Data source (e.g. filepath, stream, ...)
        """
        if not source or hasattr(source, "read") or not base_path:
            self.source = source
        else:
            self.source = Path(base_path).joinpath(source)
        if base_path:
            self.base_path = Path(base_path)
        elif isinstance(source, (str, Path)):
            self.base_path = Path(source).parent
        else:
            self.base_path = None

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
