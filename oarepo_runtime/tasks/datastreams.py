from typing import Dict, List
import celery
from oarepo_runtime.datastreams.datastreams import (
    AbstractDataStream,
    DataStreamResult,
    StreamEntry,
)
from oarepo_runtime.datastreams.config import (
    DATASTREAM_READERS,
    DATASTREAMS_TRANSFORMERS,
    DATASTREAMS_WRITERS,
    get_instance,
)
from oarepo_runtime.datastreams.transformers import BatchTransformer
from oarepo_runtime.datastreams.writers import BatchWriter
from oarepo_runtime.datastreams.errors import WriterError
import traceback
from celery.canvas import chunks, chain, Signature


@celery.shared_task
def process_datastream_transformer(transformer_definition, entries: List[StreamEntry]):
    transformer = get_instance(
        config_section=DATASTREAMS_TRANSFORMERS,
        clz="transformer",
        entry=transformer_definition,
    )
    if isinstance(transformer, BatchTransformer):
        return transformer.apply_batch(entries)
    else:
        result = []
        for entry in entries:
            try:
                result.append(transformer.apply(entry))
            except Exception as e:
                entry.filtered = True
                entry.errors.append(
                    f"Transformer {transformer_definition} error: {e}: {traceback.format_stack()}"
                )
                result.append(entry)
        return result


class AsyncDataStreamResult(DataStreamResult):
    def __init__(self, result):
        self._result = result
        self._ok_count = None
        self._failed_count = None
        self._skipped_count = None
        self._failed_entries = []

    def prepare_result(self):
        if self._ok_count is not None:
            return
        data = self._result.get()
        self._ok_count = 0
        self._failed_count = 0
        self._skipped_count = 0
        d: DataStreamResult
        for d in data:
            self._ok_count += d.ok_count
            self._failed_count += d.failed_count
            self._skipped_count += d.skipped_count
            self._failed_entries.extend(d.failed_entries or [])

    @property
    def ok_count(self):
        self.prepare_result()
        return self._ok_count

    @property
    def failed_count(self):
        self.prepare_result()
        return self._failed_count

    @property
    def skipped_count(self):
        self.prepare_result()
        return self._skipped_count

    @property
    def failed_entries(self):
        return self._failed_entries


@celery.shared_task
def process_datastream_writers(writer_definition, entries: List[StreamEntry]):
    writer = get_instance(
        config_section=DATASTREAMS_WRITERS,
        clz="writer",
        entry=writer_definition,
    )
    if isinstance(writer, BatchWriter):
        return writer.write_batch(entries)
    else:
        result = []
        for entry in entries:
            result.append(entry)
            try:
                writer.write(entry)
            except WriterError as e:
                entry.errors.append(
                    f"Writer {writer_definition} error: {e}: {traceback.format_stack()}"
                )
        return result


@celery.shared_task
def process_datastream_outcome(
    success_callback: Signature, error_callback: Signature, entries: List[StreamEntry]
):
    for entry in entries:
        if entry.errors:
            error_callback.apply((entry,))
        else:
            success_callback.apply((entry,))


class AsyncDataStream(AbstractDataStream):
    def __init__(
        self,
        *,
        readers: List[Dict],
        writers: List[Dict],
        transformers: List[Dict],
        success_callback: Signature,
        error_callback: Signature,
        batch_size=100,
        **kwargs,
    ):
        super().__init__(
            readers=readers,
            writers=writers,
            transformers=transformers,
            success_callback=success_callback,
            error_callback=error_callback,
            **kwargs,
        )
        self.batch_size = batch_size

    def process(self, max_failures=100) -> DataStreamResult:
        def read_entries():
            """Read the entries."""
            for reader_def in self._readers:
                reader = get_instance(
                    config_section=DATASTREAM_READERS,
                    clz="reader",
                    entry=reader_def,
                )

                for rec in iter(reader):
                    yield rec

        chain_def = []
        if self._transformers:
            for transformer in self._transformers:
                chain_def.append(
                    process_datastream_transformer.signature((transformer,))
                )

        chain_def.append(process_datastream_writers.signature((self._writers,)))
        chain_def.append(
            process_datastream_outcome.signature(
                (self._success_callback, self._error_callback)
            )
        )

        process = chunks(chain(*chain_def), read_entries(), self.batch_size).group()
        result = process()

        # return an empty result as we can not say how it ended
        return DataStreamResult(
            ok_count=None,
            failed_count=None,
            skipped_count=None,
            failed_entries=None,
        )
