from abc import ABC, abstractmethod

from oarepo_runtime.datastreams.batch import StreamBatch

from .datastreams import StreamEntry


class BaseTransformer(ABC):
    """Base transformer."""

    def __init__(self, **kwargs) -> None:
        pass

    @abstractmethod
    def apply(self, stream_entry: StreamEntry, *args, **kwargs) -> StreamEntry:
        """Applies the transformation to the entry.
        :returns: A StreamEntry. The transformed entry.
                  Raises TransformerError in case of errors.
        """


class BatchTransformer(ABC):
    def __init__(self, **kwargs) -> None:
        """Extra parameters for extensions"""

    @abstractmethod
    def apply_batch(self, batch: StreamBatch, *args, **kwargs) -> StreamBatch:
        """Applies the transformation to the entry.
        :returns: the same or a new batch. In case there are errors in entry transformation,
        must not raise the errors but instead set error flag & exception on the stream entry.
        Failed entries should not be removed from the batch
        """

    def apply(self, stream_entry: StreamEntry, *args, **kwargs) -> StreamEntry:
        return self.apply_batch([stream_entry], *args, **kwargs)
