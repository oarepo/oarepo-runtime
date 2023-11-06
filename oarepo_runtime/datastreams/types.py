#
# This package was taken from Invenio vocabularies and modified to be more universal
#
import dataclasses
import json
import logging
import textwrap
import traceback
from typing import Any, Dict, List, Optional, Union

from .errors import DataStreamError
from .json import JSONObject

log = logging.getLogger("datastreams")


@dataclasses.dataclass
class StreamEntryError:
    code: str
    message: str
    location: Optional[str] = None
    info: Union[JSONObject, None] = None

    @classmethod
    def from_exception(
        cls, exc: Exception, limit=30, message=None, location=None, info=None, code=None
    ):
        if isinstance(exc, DataStreamError):
            return cls(
                code=exc.code,
                message=exc.message,
                location=exc.location,
                info=exc.detail,
            )

        # can not use format_exception here as the signature is different for python 3.9 and python 3.10
        stack = traceback.format_exc(limit=limit)
        if message:
            formatted_exception = message
        elif hasattr(exc, "format_exception"):
            formatted_exception = exc.format_exception()
        else:
            formatted_exception = str(exc)

        return cls(
            code=code or getattr(exc, "type", type(exc).__name__),
            message=formatted_exception,
            location=location,
            info={
                "message": str(exc),
                "exception": type(exc).__name__,
                "stack": stack,
                **(info or {}),
            },
        )

    @property
    def json(self) -> JSONObject:
        ret = {}
        if self.code:
            ret["code"] = self.code
        if self.message:
            ret["message"] = self.message
        if self.location:
            ret["location"] = self.location
        if self.info:
            ret["info"] = self.info
        return ret

    @classmethod
    def from_json(cls, js: JSONObject):
        if js is None:
            return None
        return cls(
            code=js.get("code"),
            message=js.get("message"),
            location=js.get("location"),
            info=js.get("info"),
        )

    def __str__(self):
        formatted_info = textwrap.indent(
            json.dumps(self.info or {}, ensure_ascii=False, indent=4), prefix="    "
        )
        return f"{self.code}:{self.location if self.location else ''} {self.message}\n{formatted_info}"

    def __repr__(self):
        return str(self)


@dataclasses.dataclass
class StreamEntryFile:
    metadata: JSONObject
    content_url: str
    "data url with the content of the file or any other resolvable url"

    @property
    def json(self) -> JSONObject:
        return {
            "metadata": self.metadata,
            "content_url": self.content_url,
        }

    @classmethod
    def from_json(cls, js: JSONObject):
        return cls(
            metadata=js["metadata"],
            content_url=js["content_url"],
        )


@dataclasses.dataclass
class StreamEntry:
    """Object to encapsulate streams processing."""

    entry: JSONObject
    files: List[StreamEntryFile] = dataclasses.field(default_factory=list)
    seq: int = 0
    id: Optional[str] = None
    filtered: bool = False
    deleted: bool = False
    errors: List[StreamEntryError] = dataclasses.field(default_factory=list)
    context: JSONObject = dataclasses.field(default_factory=dict)

    @property
    def ok(self):
        return not self.filtered and not self.errors

    @property
    def json(self) -> JSONObject:
        return {
            "id": self.id,
            "entry": self.entry,
            "filtered": self.filtered,
            "deleted": self.deleted,
            "errors": [x.json for x in self.errors],
            "context": self.context,
            "seq": self.seq,
            "files": [x.json for x in self.files],
        }

    @classmethod
    def from_json(cls, js):
        return cls(
            id=js["id"],
            entry=js["entry"],
            filtered=js["filtered"],
            deleted=js["deleted"],
            errors=[StreamEntryError.from_json(x) for x in js["errors"]],
            context=js["context"],
            seq=js["seq"],
            files=[StreamEntryFile.from_json(x) for x in js["files"]],
        )

    def __str__(self):
        ret = [
            f"Entry #{self.seq}: id {self.id or 'not yet set'}, filtered: {self.filtered}, deleted: {self.deleted}",
            f"Content:",
            textwrap.indent(
                json.dumps(self.entry, ensure_ascii=False, indent=4), "    "
            ),
            f"Context:",
            textwrap.indent(
                json.dumps(self.context, ensure_ascii=False, indent=4), "    "
            ),
        ]
        if self.errors:
            ret.append("Errors:")
            for error in self.errors:
                ret.append(textwrap.indent(str(error), "    "))
        return "\n".join(ret)


@dataclasses.dataclass
class StreamBatch:
    entries: List[StreamEntry]
    context: Dict[str, Any] = dataclasses.field(default_factory=dict)
    last: bool = False
    seq: int = 0
    errors: List[StreamEntryError] = dataclasses.field(default_factory=list)

    @property
    def ok_entries(self):
        if self.errors:
            return []
        return [x for x in self.entries if x.ok]

    @property
    def failed_entries(self):
        if self.errors:
            return self.entries
        return [x for x in self.entries if x.errors]

    @property
    def skipped_entries(self):
        if self.errors:
            return []
        return [x for x in self.entries if x.filtered]

    @property
    def deleted_entries(self):
        if self.errors:
            return []
        return [x for x in self.entries if x.deleted]

    @property
    def json(self):
        return {
            "entries": [x.json for x in self.entries],
            "context": self.context,
            "last": self.last,
            "seq": self.seq,
            "errors": [x.json for x in self.errors],
        }

    @classmethod
    def from_json(cls, js):
        if js is None:
            return None
        try:
            [StreamEntry.from_json(x) for x in js["entries"]]
        except:
            log.exception("Exception parsing %s", js)
            raise
        return cls(
            entries=[StreamEntry.from_json(x) for x in js["entries"]],
            context=js["context"],
            last=js["last"],
            seq=js["seq"],
            errors=[StreamEntryError.from_json(x) for x in js["errors"]],
        )


class DataStreamCallback:
    def __init__(self, log_error_entry=False):
        self.log_error_entry = log_error_entry

    def batch_started(self, batch):
        log.info("Batch started: %s", batch)

    def batch_finished(self, batch):
        log.info("Batch finished: %s", batch)
        for err in batch.errors:
            log.error("Failed batch: %s: %s", err, batch)
        if self.log_error_entry:
            for entry in batch.entries:
                if entry.errors:
                    log.error("Failed entry: %s", entry)

    def reader_error(self, reader, exception):
        log.error("Reader error: %s: %s", reader, exception)

    def transformer_error(self, batch, transformer, exception):
        log.error("Transformer error: %s: %s", transformer, exception)

    def writer_error(self, batch, writer, exception):
        log.error("Writer error: %s: %s", writer, exception)


class StatsKeepingDataStreamCallback(DataStreamCallback):
    def __init__(self, log_error_entry=False):
        super().__init__(log_error_entry=log_error_entry)

        self.started_batches_count = 0
        self.finished_batches_count = 0
        self.ok_entries_count = 0
        self.filtered_entries_count = 0
        self.deleted_entries_count = 0
        self.failed_entries_count = 0
        self.reader_errors_count = 0
        self.transformer_errors_count = 0
        self.writer_errors_count = 0

    def batch_started(self, batch):
        super().batch_started(batch)
        self.started_batches_count += 1

    def batch_finished(self, batch: StreamBatch):
        super().batch_finished(batch)
        self.finished_batches_count += 1
        for entry in batch.entries:
            if entry.ok:
                self.ok_entries_count += 1
            if entry.filtered:
                self.filtered_entries_count += 1
            if entry.deleted:
                self.deleted_entries_count += 1
            if entry.errors:
                self.failed_entries_count += 1

    def reader_error(self, reader, exception):
        super().reader_error(reader, exception)
        self.reader_errors_count += 1

    def transformer_error(self, batch, transformer, exception):
        super().transformer_error(batch, transformer, exception)
        self.transformer_errors_count += 1

    def writer_error(self, batch, writer, exception):
        super().writer_error(batch, writer, exception)
        self.writer_errors_count += 1

    def stats(self):
        ret = [f"{self.finished_batches_count} batches finished"]
        if self.ok_entries_count:
            ret.append(f"ok: {self.ok_entries_count}")
        if self.deleted_entries_count:
            ret.append(f"deleted: {self.deleted_entries_count}")
        if self.filtered_entries_count:
            ret.append(f"filtered: {self.filtered_entries_count}")
        if self.failed_entries_count:
            ret.append(f"failed: {self.failed_entries_count}")
        if self.reader_errors_count:
            ret.append(f"reader errors: {self.reader_errors_count}")
        if self.transformer_errors_count:
            ret.append(f"transformer errors: {self.transformer_errors_count}")
        if self.writer_errors_count:
            ret.append(f"writer errors: {self.writer_errors_count}")
        return ", ".join(ret)
