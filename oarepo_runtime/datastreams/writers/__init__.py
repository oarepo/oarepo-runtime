from abc import ABC, abstractmethod
from typing import Union

from oarepo_runtime.datastreams.types import StreamBatch


class BaseWriter(ABC):
    """Base writer."""

    def __init__(self, **kwargs) -> None:
        """kwargs for extensions"""

    @abstractmethod
    def write(self, batch: StreamBatch) -> Union[StreamBatch, None]:
        """Writes the input entry to the target output.
        :returns: nothing
                  Raises WriterException in case of errors.
        """

    def finish(self):
        pass
