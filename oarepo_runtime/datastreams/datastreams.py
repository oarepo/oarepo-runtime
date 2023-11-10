import abc
import copy
import dataclasses
from enum import Enum
from typing import Any, Callable, Iterator, List, Union

from invenio_access.permissions import system_identity

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

    def resolve(self, *, identity, **kwargs):
        if self.kind == SignatureKind.TRANSFORMER:
            return current_datastreams.get_transformer(
                self, **kwargs, identity=identity
            )
        elif self.kind == SignatureKind.WRITER:
            return current_datastreams.get_writer(self, **kwargs, identity=identity)
        else:
            raise ValueError(f"Unknown signature kind: {self.kind}")


class AbstractDataStream(abc.ABC):
    def __init__(
        self,
        *,
        readers: List[Union[Signature, Any]],
        writers: List[Union[Signature, Any]],
        transformers: List[Union[Signature, Any]] = None,
        callback: Union[DataStreamCallback, Signature],
        batch_size=1,
        identity=system_identity,
        reader_callback: Callable[[StreamBatch], None] = None,
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
        self._identity = identity
        self._reader_callback = reader_callback

    def _read_entries(self) -> Iterator[StreamEntry]:
        seq = 0
        for reader_signature in self._readers:
            reader = current_datastreams.get_reader(
                reader_signature, identity=self._identity
            )
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
                batch = batch_maker()
                if self._reader_callback:
                    self._reader_callback(batch)
                yield batch
                batch_entries = []
            batch_entries.append(entry)
        batch = batch_maker(last=True)
        if self._reader_callback:
            self._reader_callback(batch)
        yield batch

    def process(self, context=None, identity=system_identity):
        context = context or {}
        chain = self.build_chain(identity)
        for batch in self._read_batches(context):
            chain.process(batch, self._callback)

    @abc.abstractmethod
    def build_chain(self, identity) -> DataStreamChain:
        pass

    def _reader_error(self, reader, exception):
        self._callback.reader_error(reader, exception=exception)
