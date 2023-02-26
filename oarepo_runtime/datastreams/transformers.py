from abc import ABC, abstractmethod


class BaseTransformer(ABC):
    """Base transformer."""

    def __init__(self, log) -> None:
        self._log = log

    @abstractmethod
    def apply(self, stream_entry, *args, **kwargs):
        """Applies the transformation to the entry.
        :returns: A StreamEntry. The transformed entry.
                  Raises TransformerError in case of errors.
        """
