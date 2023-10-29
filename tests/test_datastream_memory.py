import os
import random
import sys

import psutil
import pytest

from oarepo_runtime.datastreams import (
    BaseReader,
    BaseTransformer,
    BaseWriter,
    DataStream,
    StreamEntry,
    TransformerError,
    WriterError,
)
from oarepo_runtime.uow import BulkUnitOfWork


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


def test_oom():
    entry_size = 10000000
    readers = [OOMTestReader(1000, entry_size)]
    writers = [OOMTestWriter(error_rate=0.5)]
    transformers = [OOMTestTransformer(error_rate=0.5, filter_rate=0.1)]

    process = psutil.Process(os.getpid())
    baseline_size = process.memory_info().rss
    max_size = baseline_size

    def progress(read, written, failed):
        nonlocal max_size
        actual_size = process.memory_info().rss
        if actual_size > max_size:
            max_size = actual_size

    datastream: DataStream = DataStream(
        readers=readers,
        writers=writers,
        transformers=transformers,
        progress_callback=progress,
    )
    result = datastream.process()
    print(result)
    print(
        f"Memory increased {(max_size - baseline_size) / (entry_size * sys.getsizeof(1))} * "
        f"stream entry size {entry_size}. Up to 10 times is considered ok."
    )
    assert (max_size - baseline_size) / (entry_size * sys.getsizeof(1)) < 10


def test_batch_uow(app, db, search_clear):
    entry_size = 10000
    readers = [OOMTestReader(1000, entry_size)]
    writers = [OOMTestWriter(error_rate=0.5)]

    process = psutil.Process(os.getpid())
    baseline_size = process.memory_info().rss
    max_size = baseline_size

    def progress(read, written, failed):
        nonlocal max_size
        actual_size = process.memory_info().rss
        if actual_size > max_size:
            max_size = actual_size

    datastream: DataStream = DataStream(
        readers=readers,
        writers=writers,
        progress_callback=progress,
        uow_class=BulkUnitOfWork,
        batch_size=100,
    )
    result = datastream.process()
    print(result)
    print(
        f"Memory increased {(max_size - baseline_size) / (entry_size * sys.getsizeof(1))} * "
        f"stream entry size {entry_size}. Up to 10 times is considered ok."
    )
    assert (max_size - baseline_size) / (entry_size * sys.getsizeof(1)) < 10
