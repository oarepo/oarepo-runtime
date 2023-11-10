#
# This package was taken from Invenio vocabularies and modified to be more universal
#
import logging
from typing import List

from ..proxies import current_datastreams
from .datastreams import AbstractDataStream, DataStreamChain
from .transformers import BaseTransformer
from .types import DataStreamCallback, StreamEntryError
from .writers import BaseWriter

log = logging.getLogger("datastreams")


class SynchronousDataStreamChain(DataStreamChain):
    def __init__(self, transformers: List[BaseTransformer], writers: List[BaseWriter]):
        self._transformers = transformers
        self._writers = writers

    def process(self, batch, callback: DataStreamCallback):
        callback.batch_started(batch)
        for transformer in self._transformers:
            try:
                batch = transformer.apply(batch) or batch
            except Exception as ex:
                if log.getEffectiveLevel():
                    log.error(
                        "Unexpected error in transformer: %s: %s",
                        repr(transformer),
                        repr(batch),
                    )
                batch.errors.append(StreamEntryError.from_exception(ex))
                callback.transformer_error(batch, transformer, exception=ex)

        for writer in self._writers:
            try:
                batch = writer.write(batch) or batch
            except Exception as ex:
                if log.getEffectiveLevel():
                    log.error(
                        "Unexpected error in writer: %s: %s", repr(writer), repr(batch)
                    )
                batch.errors.append(StreamEntryError.from_exception(ex))
                callback.writer_error(batch, writer, exception=ex)
        callback.batch_finished(batch)

    def finish(self, callback: DataStreamCallback):
        for writer in self._writers:
            try:
                writer.finish()
            except Exception as e:
                log.error("Unexpected error in writer: %s", repr(writer))
                callback.writer_error(batch=None, writer=writer, exception=e)


class SynchronousDataStream(AbstractDataStream):
    """Data stream."""

    def build_chain(self, identity) -> DataStreamChain:
        return SynchronousDataStreamChain(
            transformers=[
                current_datastreams.get_transformer(tr, identity=identity)
                for tr in self._transformers
            ],
            writers=[
                current_datastreams.get_writer(wr, identity=identity)
                for wr in self._writers
            ],
        )
