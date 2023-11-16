import sys
from pathlib import Path

from oarepo_runtime.datastreams import (
    JSONObject,
    SemiAsynchronousDataStream,
    StreamBatch,
)
from oarepo_runtime.datastreams.asynchronous import deserialize_identity
from oarepo_runtime.datastreams.datastreams import Signature, SignatureKind
from oarepo_runtime.datastreams.types import StreamEntryError
from records2.proxies import current_service
from records2.records.api import Records2Record


def test_semiasync_fixtures_in_process(
    celery_app, db, app, identity, search_clear, location
):
    writer = Signature(
        kind=SignatureKind.WRITER, name="service", kwargs={"service": "records2"}
    )
    reader = Signature(
        SignatureKind.READER,
        name="yaml",
        kwargs={
            "source": str(Path(__file__).parent / "pkg_data" / f"async_records.yaml")
        },
    )

    transformer = Signature(SignatureKind.TRANSFORMER, name="status", kwargs={})

    failed_entries = set()
    filtered_entries = set()

    @celery_app.task
    def callback(
        *,
        batch: JSONObject = None,
        identity: JSONObject = None,
        callback: str = None,
        exception: JSONObject = None,
        **kwargs,
    ):
        batch = StreamBatch.from_json(batch)
        identity = deserialize_identity(identity)
        exception = StreamEntryError.from_json(exception) if exception else None

        if exception:
            print(callback, batch, identity, exception)
            sys.stdout.flush()

        if callback == "batch_finished":
            for entry in batch.entries:
                if entry.errors:
                    failed_entries.add(entry.entry["metadata"]["title"])
                elif entry.filtered:
                    filtered_entries.add(entry.entry["metadata"]["title"])

    ds = SemiAsynchronousDataStream(
        readers=[reader],
        writers=[writer],
        transformers=[transformer],
        callback=callback.s(),
        on_background=False,
    )
    ds.process()

    Records2Record.index.refresh()
    titles = set()
    for rec in current_service.scan(identity):
        titles.add(rec["metadata"]["title"])
    assert titles == {"pkg record 2", "pkg record 1"}
    assert failed_entries == {"pkg record 3"}
    assert filtered_entries == {"pkg record 4"}


def test_semiasync_failing_writer_in_process(
    celery_app, db, app, identity, search_clear, location
):
    writer = Signature(kind=SignatureKind.WRITER, name="failing", kwargs={})
    reader = Signature(
        SignatureKind.READER,
        name="yaml",
        kwargs={
            "source": str(Path(__file__).parent / "pkg_data" / f"async_records.yaml")
        },
    )

    writer_error_occured = False

    @celery_app.task
    def callback(
        *,
        batch: JSONObject = None,
        identity: JSONObject = None,
        callback: str = None,
        exception: JSONObject = None,
        **kwargs,
    ):
        nonlocal writer_error_occured
        if callback == "writer_error":
            writer_error_occured = True
        if exception:
            print(callback, batch, identity, exception)
            sys.stdout.flush()

    ds = SemiAsynchronousDataStream(
        readers=[reader],
        writers=[writer],
        callback=callback.s(),
        on_background=False,
    )
    ds.process()

    assert writer_error_occured, "Writer error should occur but was not detected"
