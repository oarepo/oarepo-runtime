import logging
import os
import random
import sys

import psutil
import pytest

from oarepo_runtime.datastreams import (
    BaseReader,
    BaseTransformer,
    BaseWriter,
    StreamEntry,
    SynchronousDataStream,
    TransformerError,
    WriterError,
)
from oarepo_runtime.datastreams.fixtures import FixturesCallback
from oarepo_runtime.datastreams.synchronous import log
from oarepo_runtime.datastreams.types import StatsKeepingDataStreamCallback

process = psutil.Process(os.getpid())


class MemoryKeepingCallback(FixturesCallback):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.baseline_size = process.memory_info().rss
        self.max_size = self.baseline_size

    def batch_finished(self, batch):
        actual_size = process.memory_info().rss
        if actual_size > self.max_size:
            self.max_size = actual_size


class OOMTestReader(BaseReader):
    def __init__(self, count, size):
        self.count = count
        self.size = size
        super().__init__()

    def __iter__(self):
        for c in range(self.count):
            yield StreamEntry(entry=[c] * self.size)


class OOMTestWriter(BaseWriter):
    def __init__(self, error_rate):
        self.error_rate = error_rate
        super().__init__()

    def write(self, entry: StreamEntry, uow=None, *args, **kwargs):
        if random.random() < self.error_rate:
            raise WriterError("Writer error in write")

    def delete(self, entry: StreamEntry, uow=None, *args, **kwargs):
        if random.random() < self.error_rate:
            raise WriterError("Writer error in delete")


class OOMTestTransformer(BaseTransformer):
    def __init__(self, error_rate, filter_rate):
        self.error_rate = error_rate
        self.filter_rate = error_rate
        super().__init__()

    def apply(self, stream_entry: StreamEntry, *args, **kwargs) -> StreamEntry:
        if random.random() < self.error_rate:
            raise TransformerError("Transformer error")
        if random.random() < self.filter_rate:
            stream_entry.filtered = True
        return stream_entry


@pytest.mark.oom
def test_oom(app, db, search_clear):
    # disable logging as pytest captures this and it will increase the memory usage immensely
    log.level = logging.CRITICAL
    try:
        run_datastream(5, 10000)

        callback = run_datastream(1000, 10000)
        print(callback.stats())
        print(
            f"Memory increased {(callback.max_size - callback.baseline_size) / (10000 * sys.getsizeof(1))} * "
            f"stream entry size {10000}. Up to 10 times is considered ok."
        )
        assert (callback.max_size - callback.baseline_size) / (
            10000 * sys.getsizeof(1)
        ) < 10
    finally:
        log.level = 0


def run_datastream(entries_count, entry_size):
    readers = [OOMTestReader(entries_count, entry_size)]
    writers = [OOMTestWriter(error_rate=0.5)]
    transformers = [OOMTestTransformer(error_rate=0.5, filter_rate=0.1)]
    callback = MemoryKeepingCallback()
    datastream = SynchronousDataStream(
        readers=readers,
        writers=writers,
        transformers=transformers,
        callback=callback,
    )
    datastream.process()
    return callback


def test_batch_uow(app, db, search_clear):
    # disable logging as pytest captures this and it will increase the memory usage immensely
    log.level = logging.CRITICAL
    try:
        run_datastream(5, 10000)

        entry_size = 10000
        readers = [OOMTestReader(1000, entry_size)]
        writers = [OOMTestWriter(error_rate=0.5)]

        callback = MemoryKeepingCallback()

        batch_size = 100

        datastream = SynchronousDataStream(
            readers=readers,
            writers=writers,
            callback=callback,
            batch_size=batch_size,
        )
        result = datastream.process()
        print(result)
        print(
            f"Memory increased {(callback.max_size - callback.baseline_size) / (entry_size * sys.getsizeof(1)) / batch_size} * "
            f"stream entry size {entry_size} per item. Up to 10 times is considered ok."
        )
        assert (callback.max_size - callback.baseline_size) / (
            entry_size * sys.getsizeof(1)
        ) < batch_size * 10

    finally:
        log.level = 0
