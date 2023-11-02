from abc import ABC, abstractmethod
from typing import Union

from oarepo_runtime.datastreams.types import StreamBatch


class BaseTransformer(ABC):
    """Base transformer."""

    def __init__(self, **kwargs) -> None:
        pass

    @abstractmethod
    def apply(self, batch: StreamBatch, *args, **kwargs) -> Union[StreamBatch, None]:
        """Applies the transformation to the entry.
        :returns: A StreamEntry. The transformed entry.
                  Raises TransformerError in case of errors.
        """
