import traceback
from typing import Dict, List

import celery
from celery.canvas import Signature, chain

from oarepo_runtime.datastreams.batch import StreamBatch
from oarepo_runtime.datastreams.config import (
    DATASTREAM_READERS,
    DATASTREAMS_TRANSFORMERS,
    DATASTREAMS_WRITERS,
    get_instance,
)
from oarepo_runtime.datastreams.datastreams import (
    AbstractDataStream,
    DataStreamResult,
    StreamEntry,
)
from oarepo_runtime.datastreams.errors import TransformerError, WriterError
from oarepo_runtime.datastreams.transformers import BatchTransformer
from oarepo_runtime.datastreams.writers import BatchWriter


@celery.shared_task
def process_datastream_transformer(_batch: Dict, *, transformer_definition):
    batch: StreamBatch = _deserialize_batch(_batch)
    transformer = get_instance(
        config_section=DATASTREAMS_TRANSFORMERS,
        clz="transformer",
        entry=transformer_definition,
    )
    if isinstance(transformer, BatchTransformer):
        return _serialize_batch(transformer.apply_batch(batch))
    else:
        result = []
        for entry in batch.entries:
            try:
                result.append(transformer.apply(entry))
            except TransformerError as e:
                stack = "\n".join(traceback.format_stack())
                entry.errors.append(
                    f"Transformer {transformer_definition} error: {e}: {stack}"
                )
                result.append(entry)
            except Exception as e:
                stack = "\n".join(traceback.format_stack())
                entry.errors.append(
                    f"Transformer {transformer_definition} unhandled error: {e}: {stack}"
                )
                result.append(entry)
        batch.entries = result
        return _serialize_batch(batch)


@celery.shared_task
def process_datastream_writers(_batch: Dict, *, writer_definitions):
    batch: StreamBatch = _deserialize_batch(_batch)
    for wd in writer_definitions:
        writer = get_instance(
            config_section=DATASTREAMS_WRITERS,
            clz="writer",
            entry=wd,
        )
        if isinstance(writer, BatchWriter):
            writer.write_batch(batch)
        else:
            for entry in batch.entries:
                if entry.ok:
                    try:
                        writer.write(entry)
                    except WriterError as e:
                        stack = "\n".join(traceback.format_stack())
                        entry.errors.append(f"Writer {wd} error: {e}: {stack}")
                    except Exception as e:
                        stack = "\n".join(traceback.format_stack())
                        entry.errors.append(
                            f"Writer {wd} unhandled error: {e}: {stack}"
                        )
    return _serialize_batch(batch)


@celery.shared_task
def process_datastream_outcome(
    _batch: Dict,
    *,
    success_callback: Signature,
    error_callback: Signature,
):
    ok_count = 0
    skipped_count = 0
    failed_count = 0
    failed_entries = []
    batch: StreamBatch = _deserialize_batch(_batch)
    entry: StreamEntry
    for entry in batch.entries:
        if entry.errors:
            error_callback.apply((entry,))
            failed_count += 1
            failed_entries.append(entry)
        else:
            success_callback.apply((entry,))
            if entry.filtered:
                skipped_count += 1
            else:
                ok_count += 1

    return _serialize_datastream_result(
        DataStreamResult(
            ok_count=ok_count,
            failed_count=failed_count,
            skipped_count=skipped_count,
            failed_entries=failed_entries,
        )
    )


class AsyncDataStreamResult(DataStreamResult):
    def __init__(self, results):
        self._results = results
        self._ok_count = None
        self._failed_count = None
        self._skipped_count = None
        self._failed_entries = []

    def prepare_result(self):
        if self._ok_count is not None:
            return
        self._ok_count = 0
        self._failed_count = 0
        self._skipped_count = 0
        for result in self._results:
            d = _deserialize_datastream_result(result.get())
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
        in_process=False,
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
        self.in_process = in_process

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
                    process_datastream_transformer.signature(
                        kwargs={"transformer_definition": transformer}
                    )
                )

        chain_def.append(
            process_datastream_writers.signature(
                kwargs={"writer_definitions": self._writers}
            )
        )
        chain_def.append(
            process_datastream_outcome.signature(
                kwargs={
                    "success_callback": self._success_callback,
                    "error_callback": self._error_callback,
                }
            )
        )

        chain_sig = chain(*chain_def)
        chain_sig.link_error(self._error_callback)

        results = []
        batch_entries = []
        batch_sequence_no = 1

        if self.in_process:
            call = chain_sig.apply
        else:
            call = chain_sig.apply_async

        for entry in read_entries():
            batch_entries.append(entry)
            if len(batch_entries) == self.batch_size:
                batch = StreamBatch(
                    seq=batch_sequence_no, entries=batch_entries, last=False, context={}
                )
                batch_sequence_no += 1
                results.append(call((_serialize_batch(batch),)))
                batch_entries = []

        batch = StreamBatch(
            seq=batch_sequence_no, entries=batch_entries, last=True, context={}
        )
        results.append(call((_serialize_batch(batch),)))

        # return an async result as we can not say how it ended
        return AsyncDataStreamResult(results)


def _serialize_entries(batch: List[StreamEntry]):
    return [
        {
            "entry": x.entry,
            "filtered": x.filtered,
            "errors": x.errors,
            "context": x.context,
        }
        for x in batch
    ]


def _deserialize_entries(_entries: List[Dict]):
    return [
        StreamEntry(
            entry=x["entry"],
            filtered=x["filtered"],
            errors=x["errors"],
            context=x["context"],
        )
        for x in _entries
    ]


def _serialize_datastream_result(result: DataStreamResult):
    return {
        "ok_count": result.ok_count,
        "failed_count": result.failed_count,
        "skipped_count": result.skipped_count,
        "failed_entries": _serialize_entries(result.failed_entries),
    }


def _deserialize_datastream_result(result: Dict):
    return DataStreamResult(
        ok_count=result["ok_count"],
        failed_count=result["failed_count"],
        skipped_count=result["skipped_count"],
        failed_entries=_deserialize_entries(result["failed_entries"]),
    )


def _deserialize_batch(_batch: Dict):
    return StreamBatch(
        seq=_batch["seq"],
        last=_batch["last"],
        entries=_deserialize_entries(_batch["entries"]),
        context=_batch["context"],
    )


def _serialize_batch(batch: StreamBatch):
    return {
        "seq": batch.seq,
        "last": batch.last,
        "entries": _serialize_entries(batch.entries),
        "context": batch.context,
    }
