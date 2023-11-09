from io import StringIO
from pathlib import Path

from oarepo_runtime.datastreams import StreamEntry
from oarepo_runtime.datastreams.readers.excel import ExcelReader
from oarepo_runtime.datastreams.readers.json import JSONLinesReader, JSONReader
from oarepo_runtime.datastreams.readers.yaml import YamlReader
from oarepo_runtime.datastreams.types import StreamEntryFile


def test_json_datastream_reader():
    reader = JSONReader(source=StringIO('[{"a": 1}]'))
    data = list(reader)
    assert data == [StreamEntry({"a": 1})]


def test_yaml_datastream_reader():
    reader = YamlReader(
        source=StringIO(
            """
a: 1
---
a: 2    
    """
        )
    )
    data = list(reader)
    assert data == [StreamEntry({"a": 1}), StreamEntry({"a": 2})]


def test_jsonlines_reader():
    reader = JSONLinesReader(source=StringIO('{"a": 1}\n{"a": 2}\n'))
    data = list(reader)
    assert data == [StreamEntry({"a": 1}), StreamEntry({"a": 2})]


def test_excel_reader():
    reader = ExcelReader(source=Path(__file__).parent / "data" / "records.xlsx")
    data = list(reader)
    assert set(x.entry["id"] for x in data) == {"c_abf2", "c_f1cf", "c_16ec", "c_14cb"}


def test_attachment_reader():
    reader = YamlReader(source=Path(__file__).parent / "file_data" / "records2.yaml")
    data = list(reader)
    assert data == [
        StreamEntry(
            entry={
                "$schema": "local://records2-1.0.0.json",
                "created": "2023-07-27T09:02:25.742266+00:00",
                "files": {"enabled": True},
                "id": "cvwj4-2j776",
                "links": {"files": "cvwj4-2j776/files", "self": "cvwj4-2j776"},
                "metadata": {"title": "blah"},
                "revision_id": 2,
                "updated": "2023-07-27T09:02:25.758914+00:00",
            },
            files=[
                StreamEntryFile(
                    metadata={
                        "checksum": "md5:3b11d61e470665cdd98909b95447fd19",
                        "created": "2023-07-27T09:02:25.804496+00:00",
                        "key": "test.png",
                        "mimetype": "image/png",
                        "size": 27,
                        "updated": "2023-07-27T09:02:25.912204+00:00",
                    },
                    content_url="data:iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAAAXNSR0IArs4c6QAAAJZlWElmTU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAIAAIdpAAQAAAABAAAATgAAAAAAAACQAAAAAQAAAJAAAAABAASShgAHAAAAEgAAAISgAQADAAAAAQABAACgAgAEAAAAAQAAAAygAwAEAAAAAQAAAAwAAAAAQVNDSUkAAABTY3JlZW5zaG902tFykgAAAAlwSFlzAAAWJQAAFiUBSVIk8AAAAdRpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDYuMC4wIj4KICAgPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgICAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6ZXhpZj0iaHR0cDovL25zLmFkb2JlLmNvbS9leGlmLzEuMC8iPgogICAgICAgICA8ZXhpZjpQaXhlbFlEaW1lbnNpb24+MTI8L2V4aWY6UGl4ZWxZRGltZW5zaW9uPgogICAgICAgICA8ZXhpZjpQaXhlbFhEaW1lbnNpb24+MTI8L2V4aWY6UGl4ZWxYRGltZW5zaW9uPgogICAgICAgICA8ZXhpZjpVc2VyQ29tbWVudD5TY3JlZW5zaG90PC9leGlmOlVzZXJDb21tZW50PgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4K5bXnRQAAABxpRE9UAAAAAgAAAAAAAAAGAAAAKAAAAAYAAAAGAAAASBhkRZUAAAAUSURBVCgVYpSTV/rPQAJgHIkaAAAAAP//8Mq0IQAAABFJREFUY5STV/rPQAJgHIkaAELiEHWPULDkAAAAAElFTkSuQmCC",
                ),
                StreamEntryFile(
                    metadata={
                        "checksum": "md5:e362d843bc49d5864595d6f6ec614ace",
                        "created": "2023-07-27T09:02:25.976924+00:00",
                        "key": "another.png",
                        "mimetype": "image/png",
                        "size": 30,
                        "updated": "2023-07-27T09:02:25.999255+00:00",
                    },
                    content_url="data:iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAAAXNSR0IArs4c6QAAAJZlWElmTU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAIAAIdpAAQAAAABAAAATgAAAAAAAACQAAAAAQAAAJAAAAABAASShgAHAAAAEgAAAISgAQADAAAAAQABAACgAgAEAAAAAQAAAAygAwAEAAAAAQAAAAwAAAAAQVNDSUkAAABTY3JlZW5zaG902tFykgAAAAlwSFlzAAAWJQAAFiUBSVIk8AAAAdRpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDYuMC4wIj4KICAgPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgICAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6ZXhpZj0iaHR0cDovL25zLmFkb2JlLmNvbS9leGlmLzEuMC8iPgogICAgICAgICA8ZXhpZjpQaXhlbFlEaW1lbnNpb24+MTI8L2V4aWY6UGl4ZWxZRGltZW5zaW9uPgogICAgICAgICA8ZXhpZjpQaXhlbFhEaW1lbnNpb24+MTI8L2V4aWY6UGl4ZWxYRGltZW5zaW9uPgogICAgICAgICA8ZXhpZjpVc2VyQ29tbWVudD5TY3JlZW5zaG90PC9leGlmOlVzZXJDb21tZW50PgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4K5bXnRQAAABxpRE9UAAAAAgAAAAAAAAAGAAAAKAAAAAYAAAAGAAAASBhkRZUAAAAUSURBVCgVYpSTV/rPQAJgHIkaAAAAAP//8Mq0IQAAABFJREFUY5STV/rPQAJgHIkaAELiEHWPULDkAAAAAElFTkSuQmCC",
                ),
            ],
            seq=0,
            id=None,
            filtered=False,
            deleted=False,
            errors=[],
            context={},
        ),
        StreamEntry(
            entry={
                "$schema": "local://records2-1.0.0.json",
                "created": "2023-07-27T09:02:26.014196+00:00",
                "files": {"enabled": True},
                "id": "fk75x-vcj82",
                "links": {"files": "fk75x-vcj82/files", "self": "fk75x-vcj82"},
                "metadata": {"title": "blah 2"},
                "revision_id": 2,
                "updated": "2023-07-27T09:02:26.024969+00:00",
            },
            files=[
                StreamEntryFile(
                    metadata={
                        "checksum": "md5:3b11d61e470665cdd98909b95447fd19",
                        "created": "2023-07-27T09:02:26.046219+00:00",
                        "key": "test.png",
                        "mimetype": "image/png",
                        "size": 27,
                        "updated": "2023-07-27T09:02:26.069372+00:00",
                    },
                    content_url="data:iVBORw0KGgoAAAANSUhEUgAAAAwAAAAMCAYAAABWdVznAAAAAXNSR0IArs4c6QAAAJZlWElmTU0AKgAAAAgABAEaAAUAAAABAAAAPgEbAAUAAAABAAAARgEoAAMAAAABAAIAAIdpAAQAAAABAAAATgAAAAAAAACQAAAAAQAAAJAAAAABAASShgAHAAAAEgAAAISgAQADAAAAAQABAACgAgAEAAAAAQAAAAygAwAEAAAAAQAAAAwAAAAAQVNDSUkAAABTY3JlZW5zaG902tFykgAAAAlwSFlzAAAWJQAAFiUBSVIk8AAAAdRpVFh0WE1MOmNvbS5hZG9iZS54bXAAAAAAADx4OnhtcG1ldGEgeG1sbnM6eD0iYWRvYmU6bnM6bWV0YS8iIHg6eG1wdGs9IlhNUCBDb3JlIDYuMC4wIj4KICAgPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICAgICAgPHJkZjpEZXNjcmlwdGlvbiByZGY6YWJvdXQ9IiIKICAgICAgICAgICAgeG1sbnM6ZXhpZj0iaHR0cDovL25zLmFkb2JlLmNvbS9leGlmLzEuMC8iPgogICAgICAgICA8ZXhpZjpQaXhlbFlEaW1lbnNpb24+MTI8L2V4aWY6UGl4ZWxZRGltZW5zaW9uPgogICAgICAgICA8ZXhpZjpQaXhlbFhEaW1lbnNpb24+MTI8L2V4aWY6UGl4ZWxYRGltZW5zaW9uPgogICAgICAgICA8ZXhpZjpVc2VyQ29tbWVudD5TY3JlZW5zaG90PC9leGlmOlVzZXJDb21tZW50PgogICAgICA8L3JkZjpEZXNjcmlwdGlvbj4KICAgPC9yZGY6UkRGPgo8L3g6eG1wbWV0YT4K5bXnRQAAABxpRE9UAAAAAgAAAAAAAAAGAAAAKAAAAAYAAAAGAAAASBhkRZUAAAAUSURBVCgVYpSTV/rPQAJgHIkaAAAAAP//8Mq0IQAAABFJREFUY5STV/rPQAJgHIkaAELiEHWPULDkAAAAAElFTkSuQmCC",
                )
            ],
            seq=0,
            id=None,
            filtered=False,
            deleted=False,
            errors=[],
            context={},
        ),
    ]
