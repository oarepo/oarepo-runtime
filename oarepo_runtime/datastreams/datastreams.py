#
# This package was taken from Invenio vocabularies and modified to be more universal
#
import abc
import dataclasses
import itertools
import json
import logging
import traceback
import typing
from typing import Any, Dict, List

from invenio_db import db
from invenio_records_resources.services.uow import UnitOfWork

from .errors import DataStreamError, JSONObject, TransformerError, WriterError

log = logging.getLogger("datastreams")


@dataclasses.dataclass
class StreamEntryError:
    code: str
    message: str
    location: typing.Optional[str] = None
    info: typing.Union[JSONObject, None] = None

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
    def json(self):
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
    def from_json(cls, js):
        return cls(
            code=js.get("code"),
            message=js.get("message"),
            location=js.get("location"),
            info=js.get("info"),
        )

    def __str__(self):
        formatted_info = json.dumps(self.info or {}, ensure_ascii=False, indent=4)
        return f"{self.code}:{self.location if self.location else ''} {self.message}\n{formatted_info}"

    def __repr__(self):
        return str(self)


@dataclasses.dataclass
class StreamEntry:
    """Object to encapsulate streams processing."""

    entry: Any
    filtered: bool = False
    errors: List[StreamEntryError] = dataclasses.field(default_factory=list)
    context: Dict[str, Any] = dataclasses.field(default_factory=dict)

    @property
    def ok(self):
        return not self.filtered and not self.errors


@dataclasses.dataclass
class DataStreamResult:
    ok_count: int
    failed_count: int
    skipped_count: int


def noop(*_args, **_kwargs):
    """Noop callback"""


class AbstractDataStream(abc.ABC):
    def __init__(
        self,
        *,
        readers,
        writers,
        transformers=None,
        success_callback=None,
        error_callback=None,
        progress_callback=None,
        batch_size=None,
        uow_class=None,
        **kwargs,
    ):
        """Constructor.
        :param readers: an ordered list of readers (whatever a reader is).
        :param writers: an ordered list of writers (whatever a writer is).
        :param transformers: an ordered list of transformers to apply (whatever a transformer is).
        """
        self._readers = readers
        self._transformers = transformers or []
        self._writers = writers
        self._error_callback = error_callback or noop
        self._success_callback = success_callback or noop
        self._progress_callback = progress_callback or noop
        self._batch_size = batch_size
        self._uow_class = uow_class or UnitOfWork

    @abc.abstractmethod
    def process(self) -> DataStreamResult:
        pass


class DataStream(AbstractDataStream):
    """Data stream."""

    def process(self) -> DataStreamResult:
        """Iterates over the entries.
        Uses the reader to get the raw entries and transforms them.
        It will iterate over the `StreamEntry` objects returned by
        the reader, apply the transformations and yield the result of
        writing it.
        """
        self._written, self._filtered, self._failed = 0, 0, 0
        nested = None
        uow = None
        try:
            if self._uow_class and self._batch_size:
                nested = db.session.begin_nested()
                uow = self._uow_class(session=nested)
            read_count = 0
            for stream_entry in self.read():
                read_count += 1
                self._progress_callback(
                    read=read_count, written=self._written, failed=self._failed
                )
                if stream_entry.errors:
                    self._error_callback(stream_entry)
                    self._failed += 1
                    continue
                transformed_entry = self.transform_single(stream_entry)
                if transformed_entry.errors:
                    self._error_callback(transformed_entry)
                    self._failed += 1
                    continue
                if transformed_entry.filtered:
                    self._filtered += 1
                    continue

                written_entry = self.write(transformed_entry, uow=uow)
                if written_entry.errors:
                    self._error_callback(written_entry)
                    self._failed += 1
                else:
                    self._success_callback(written_entry)
                    self._written += 1
                if self._batch_size and uow and (self._written % self._batch_size) == 0:
                    uow.commit()
                    # just to make sure we are not referencing committed nested if exception happens in the two lines
                    # below
                    nested = None
                    nested = db.session.begin_nested()
                    uow = self._uow_class(session=nested)

            if uow:
                uow.commit()
                nested = None

            return DataStreamResult(
                ok_count=self._written,
                failed_count=self._failed,
                skipped_count=self._filtered,
            )
        except:
            if nested:
                nested.rollback()
            raise

    def read(self):
        """Read the entries."""
        for rec in itertools.chain(*[iter(x) for x in self._readers]):
            yield rec

    def transform_single(self, stream_entry, *_args, **_kwargs):
        """Apply the transformations to an stream_entry."""
        for transformer in self._transformers:
            try:
                stream_entry = transformer.apply(stream_entry)
            except TransformerError as err:
                stream_entry.errors.append(StreamEntryError.from_exception(err))
                return stream_entry  # break loop
            except Exception as err:
                log.error(
                    "Unexpected error in transformer: %s: %s",
                    err,
                    repr(stream_entry.entry),
                )
                stream_entry.errors.append(StreamEntryError.from_exception(err))
                return stream_entry  # break loop

        return stream_entry

    def write(self, stream_entry, *_args, **kwargs):
        """Apply the transformations to an stream_entry."""
        for writer in self._writers:
            try:
                writer.write(stream_entry, **kwargs)
            except WriterError as err:
                stream_entry.errors.append(StreamEntryError.from_exception(err))
            except Exception as err:
                log.error(
                    "Unexpected error in writer: %s: %s", err, repr(stream_entry.entry)
                )
                stream_entry.errors.append(StreamEntryError.from_exception(err))

        return stream_entry
