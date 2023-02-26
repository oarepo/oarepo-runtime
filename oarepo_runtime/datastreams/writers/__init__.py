from abc import ABC, abstractmethod
from ..datastreams import StreamEntry


class BaseWriter(ABC):
    """Base writer."""

    def __init__(self, log, **kwargs) -> None:
        self._log = log

    @abstractmethod
    def write(self, entry: StreamEntry, *args, **kwargs):
        """Writes the input entry to the target output.
        :returns: The result of writing the entry.
                  Raises WriterException in case of errors.
        """
        pass

    def finish(self):
        """Finalizes writing"""
        pass
