from abc import ABC, abstractmethod
from typing import List
from .datastreams import StreamEntry


class BaseTransformer(ABC):
    """Base transformer."""

    def __init__(self) -> None:
        pass

    @abstractmethod
    def apply(self, stream_entry: StreamEntry, *args, **kwargs) -> StreamEntry:
        """Applies the transformation to the entry.
        :returns: A StreamEntry. The transformed entry.
                  Raises TransformerError in case of errors.
        """


class BatchTransformer(BaseTransformer):
    @abstractmethod
    def apply_batch(
        self, stream_entry: List[StreamEntry], *args, **kwargs
    ) -> List[StreamEntry]:
        """Applies the transformation to the entry.
        :returns: A StreamEntry. The transformed entry.
                  Raises TransformerError in case of errors.
        """
