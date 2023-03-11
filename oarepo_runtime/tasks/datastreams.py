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
from celery.canvas import chunks, chain, Signature, group


@celery.shared_task
def process_datastream_transformer(_entries: List[Dict], *, transformer_definition):
    entries: List[StreamEntry] = _deserialize_entries(_entries)
    transformer = get_instance(
        config_section=DATASTREAMS_TRANSFORMERS,
        clz="transformer",
        entry=transformer_definition,
    )
    if isinstance(transformer, BatchTransformer):
        return _serialize_entries(transformer.apply_batch(entries))
    else:
        result = []
        for entry in entries:
            try:
                result.append(transformer.apply(entry))
            except Exception as e:
                stack = "\n".join(traceback.format_stack())
                entry.errors.append(
                    f"Transformer {transformer_definition} error: {e}: {stack}"
                )
                result.append(entry)
        return _serialize_entries(result)


@celery.shared_task
def process_datastream_writers(_entries: List[Dict], *, writer_definitions):
    entries: List[StreamEntry] = _deserialize_entries(_entries)
    for wd in writer_definitions:
        writer = get_instance(
            config_section=DATASTREAMS_WRITERS,
            clz="writer",
            entry=wd,
        )
        if isinstance(writer, BatchWriter):
            writer.write_batch([x for x in entries if not x.errors and not x.filtered])
        else:
            for entry in entries:
                if not entry.errors and not entry.filtered:
                    try:
                        writer.write(entry)
                    except WriterError as e:
                        stack = "\n".join(traceback.format_stack())
                        entry.errors.append(f"Writer {wd} error: {e}: {stack}")
    return _serialize_entries(entries)


@celery.shared_task
def process_datastream_outcome(
    _entries: List[Dict],
    *,
    success_callback: Signature,
    error_callback: Signature,
):
    ok_count = 0
    skipped_count = 0
    failed_count = 0
    failed_entries = []
    entries: List[StreamEntry] = _deserialize_entries(_entries)
    entry: StreamEntry
    for entry in entries:
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
        batch = []

        for entry in read_entries():
            batch.append(entry)
            if len(batch) == self.batch_size:
                if self.in_process:
                    results.append(chain_sig.apply((_serialize_entries(batch),)))
                else:
                    results.append(chain_sig.apply_async((_serialize_entries(batch),)))
                batch = []
        if batch:
            if self.in_process:
                results.append(chain_sig.apply((_serialize_entries(batch),)))
            else:
                results.append(chain_sig.apply_async((_serialize_entries(batch),)))

        # return an empty result as we can not say how it ended
        return AsyncDataStreamResult(results)


def _serialize_entries(batch: List[StreamEntry]):
    return [
        {"entry": x.entry, "filtered": x.filtered, "errors": x.errors} for x in batch
    ]


def _deserialize_entries(_entries: List[Dict]):
    return [
        StreamEntry(entry=x["entry"], filtered=x["filtered"], errors=x["errors"])
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
