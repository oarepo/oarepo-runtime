from io import StringIO
from pathlib import Path
from unittest.mock import MagicMock

from oarepo_runtime.datastreams import DataStreamCallback, SynchronousDataStream
from oarepo_runtime.datastreams.datastreams import Signature
from oarepo_runtime.datastreams.readers.yaml import YamlReader
from oarepo_runtime.datastreams.writers.yaml import YamlWriter


def test_synchronous_datastream_no_reader_writer():
    test_callback = MagicMock(spec=DataStreamCallback)

    datastream = SynchronousDataStream(
        readers=[],
        transformers=[],
        writers=[],
        callback=test_callback,
    )

    datastream.process()
    assert [x[0] for x in test_callback.method_calls] == [
        "batch_started",
        "batch_finished",
    ]


def test_synchronous_datastream_reader_no_writer(app):
    test_callback = MagicMock(spec=DataStreamCallback)

    datastream = SynchronousDataStream(
        readers=[
            # you can either pass signature or an instance of the reader to synchronous datastream
            Signature(
                "reader",
                "yaml",
                kwargs={"source": Path(__file__).parent / "data" / "records.yaml"},
            )
        ],
        transformers=[],
        writers=[],
        callback=test_callback,
    )

    datastream.process()
    assert [x[0] for x in test_callback.method_calls] == [
        "batch_started",
        "batch_finished",
        "batch_started",
        "batch_finished",
    ]


def test_synchronous_datastream_reader_yaml_writer(app):
    test_callback = MagicMock(spec=DataStreamCallback)

    io = StringIO()
    datastream = SynchronousDataStream(
        # you can either pass signature or an instance of the reader to synchronous datastream
        readers=[YamlReader(source=Path(__file__).parent / "data" / "records.yaml")],
        transformers=[],
        writers=[YamlWriter(target=io)],
        callback=test_callback,
    )

    datastream.process()
    assert [x[0] for x in test_callback.method_calls] == [
        "batch_started",
        "batch_finished",
        "batch_started",
        "batch_finished",
    ]
    assert (
        io.getvalue().strip()
        == """
metadata:
  title: record 1
---
metadata:
  title: record 2    
        """.strip()
    )
