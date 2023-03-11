from abc import ABC, abstractmethod
from typing import List

from ..datastreams import StreamEntry
from ..errors import WriterError


class BaseWriter(ABC):
    """Base writer."""

    def __init__(self, **kwargs) -> None:
        pass

    @abstractmethod
    def write(self, entry: StreamEntry, *args, **kwargs):
        """Writes the input entry to the target output.
        :returns: nothing
                  Raises WriterException in case of errors.
        """

    def finish(self):
        """Finalizes writing"""


class BatchWriter(BaseWriter):
    @abstractmethod
    def write_batch(self, entry: List[StreamEntry], *args, **kwargs):
        """Writes the input entry to the target output.
        :returns: nothing
                  Raises WriterException in case of errors.
        """
