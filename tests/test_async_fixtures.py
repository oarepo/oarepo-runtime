from pathlib import Path

from oarepo_runtime.datastreams.datastreams import StreamEntry
from oarepo_runtime.tasks.datastreams import AsyncDataStream


def test_async_fixtures(celery_app, db, app, identity, search_clear, location):
    writer_config = {"writer": "service", "service": "records2"}
    reader_config = {
        "source": Path(__file__).parent / "pkg_data" / f"async_records.yaml",
        "reader": "yaml",
    }
    transformers_config = [
        {"transformer": "status"},
    ]

    stats = {"success": 0, "error": 0, "skipped": 0}

    @celery_app.task
    def success_callback(entry: StreamEntry, *args, **kwargs):
        if not entry.errors and not entry.filtered:
            stats["success"] += 1
        elif entry.filtered:
            stats["skipped"] += 1

    @celery_app.task
    def error_callback(entry, *args, **kwargs):
        print("Error:", entry, args, kwargs)
        stats["error"] += 1

    ds = AsyncDataStream(
        readers=[reader_config],
        writers=[writer_config],
        transformers=transformers_config,
        success_callback=success_callback,
        error_callback=error_callback,
    )
    result = ds.process()
    assert result.ok_count == 2
    assert result.skipped_count == 1
    assert result.failed_count == 1

    assert stats["success"] == 2
    assert stats["error"] == 1
