from abc import ABC, abstractmethod

from oarepo_runtime.datastreams.batch import StreamBatch

from ..datastreams import StreamEntry


class BaseWriter(ABC):
    """Base writer."""

    def __init__(self, **kwargs) -> None:
        """kwargs for extensions"""

    @abstractmethod
    def write(self, entry: StreamEntry, *args, **kwargs):
        """Writes the input entry to the target output.
        :returns: nothing
                  Raises WriterException in case of errors.
        """

    def finish(self):
        """Finalizes writing"""


class BatchWriter(ABC):
    def __init__(self, **kwargs) -> None:
        """kwargs for extensions"""

    @abstractmethod
    def write_batch(self, batch: StreamBatch, *args, **kwargs) -> StreamBatch:
        """Writes the batch to teh stream
        :returns: the batch written. If there are any errors writing entries
        of the batch, should mark them on entries[x].errors.

        Note: the batch contains all items, even the filtered ones or the ones
        with errors. Get StreamEntry.ok property to write only the correct batch
        entries.
        """
