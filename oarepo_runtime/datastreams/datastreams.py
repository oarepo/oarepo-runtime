import abc
import copy
import dataclasses
from enum import Enum
from typing import Any, Iterator, List, Union

from oarepo_runtime.datastreams.types import (
    DataStreamCallback,
    StreamBatch,
    StreamEntry,
)
from oarepo_runtime.proxies import current_datastreams

from .json import JSONObject


class DataStreamChain(abc.ABC):
    @abc.abstractmethod
    def process(self, batch: StreamBatch, callback: Union[DataStreamCallback, Any]):
        pass

    @abc.abstractmethod
    def finish(self, callback: Union[DataStreamCallback, Any]):
        pass


class SignatureKind(str, Enum):
    READER = "reader"
    TRANSFORMER = "transformer"
    WRITER = "writer"


@dataclasses.dataclass
class Signature:
    kind: SignatureKind
    name: str
    kwargs: JSONObject

    @property
    def json(self):
        return {"kind": self.kind.value, "name": self.name, "kwargs": self.kwargs}

    @classmethod
    def from_json(cls, json):
        return cls(
            kind=SignatureKind(json["kind"]),
            name=json["name"],
            kwargs=json["kwargs"],
        )

    def resolve(self, **kwargs):
        if self.kind == SignatureKind.TRANSFORMER:
            return current_datastreams.get_transformer(self, **kwargs)
        elif self.kind == SignatureKind.WRITER:
            return current_datastreams.get_writer(self, **kwargs)
        else:
            raise ValueError(f"Unknown signature kind: {self.kind}")


class AbstractDataStream(abc.ABC):
    def __init__(
        self,
        *,
        readers: List[Union[Signature, Any]],
        writers: List[Union[Signature, Any]],
        transformers: List[Union[Signature, Any]] = None,
        callback: Union[DataStreamCallback, Any],
        batch_size=1,
    ):
        """Constructor.
        :param readers: an ordered list of readers (whatever a reader is).
        :param writers: an ordered list of writers (whatever a writer is).
        :param transformers: an ordered list of transformers to apply (whatever a transformer is).
        """
        self._readers: List[Signature] = [*readers]
        self._transformers: List[Signature] = [*(transformers or [])]
        self._writers: List[Signature] = [*writers]
        self._callback = callback
        self._batch_size = batch_size

    def _read_entries(self) -> Iterator[StreamEntry]:
        seq = 0
        for reader_signature in self._readers:
            reader = current_datastreams.get_reader(reader_signature)
            try:
                for entry in reader:
                    seq += 1
                    entry.seq = seq
                    yield entry
            except Exception as ex:
                self._reader_error(reader, exception=ex)

    def _read_batches(self, context) -> Iterator[StreamBatch]:
        batch_entries = []
        batch_number = 0

        def batch_maker(last=False):
            nonlocal batch_number, batch_entries
            batch_number += 1
            ret = StreamBatch(
                entries=batch_entries,
                seq=batch_number,
                context=copy.deepcopy(context),
                last=last,
            )
            batch_entries = []
            return ret

        for entry in self._read_entries():
            if len(batch_entries) == self._batch_size:
                yield batch_maker()
                batch_entries = []
            batch_entries.append(entry)
        yield batch_maker(last=True)

    def process(self, context=None):
        context = context or {}
        chain = self.build_chain()
        for batch in self._read_batches(context):
            chain.process(batch, self._callback)

    @abc.abstractmethod
    def build_chain(self) -> DataStreamChain:
        pass

    def _reader_error(self, reader, exception):
        self._callback.reader_error(reader, exception=exception)
