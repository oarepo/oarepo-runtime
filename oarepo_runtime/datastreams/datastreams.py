#
# This package was taken from Invenio vocabularies and modified to be more universal
#
import dataclasses
import itertools
from typing import List

from .errors import TransformerError, WriterError


class StreamEntry:
    """Object to encapsulate streams processing."""

    def __init__(self, entry, errors=None):
        """Constructor."""
        self.entry = entry
        self.filtered = False
        self.errors = errors or []


@dataclasses.dataclass
class DataStreamResult:
    ok_count: int
    failed_count: int
    skipped_count: int
    failed_entries: List[StreamEntry]


class DataStream:
    """Data stream."""

    def __init__(self, *, readers, writers, transformers=None, log=None, **kwargs):
        """Constructor.
        :param readers: an ordered list of readers.
        :param writers: an ordered list of writers.
        :param transformers: an ordered list of transformers to apply.
        """
        self._readers = readers
        self._transformers = transformers
        self._writers = writers
        self._log = log

    def process(self, max_failures=100) -> DataStreamResult:
        """Iterates over the entries.
        Uses the reader to get the raw entries and transforms them.
        It will iterate over the `StreamEntry` objects returned by
        the reader, apply the transformations and yield the result of
        writing it.
        """
        _written, _filtered, _failed = 0, 0, 0
        failed_entries = []

        for stream_entry in self.read():
            if stream_entry.errors:
                if len(failed_entries) < max_failures:
                    _failed += 1
                    failed_entries.append(stream_entry)
                continue

            transformed_entry = self.transform(stream_entry)
            if transformed_entry.errors:
                _failed += 1
                failed_entries.append(transformed_entry)
                continue
            if transformed_entry.filtered:
                _filtered += 1
                continue

            self.write(transformed_entry)
            _written += 1

        return DataStreamResult(
            ok_count=_written,
            failed_count=_failed,
            skipped_count=_filtered,
            failed_entries=failed_entries,
        )

    def read(self):
        """Read the entries."""
        for rec in itertools.chain(*[iter(x) for x in self._readers]):
            yield rec

    def transform(self, stream_entry, *args, **kwargs):
        """Apply the transformations to an stream_entry."""
        for transformer in self._transformers:
            try:
                stream_entry = transformer.apply(stream_entry)
            except TransformerError as err:
                stream_entry.errors.append(
                    f"{transformer.__class__.__name__}: {str(err)}"
                )
                return stream_entry  # break loop

        return stream_entry

    def write(self, stream_entry, *args, **kwargs):
        """Apply the transformations to an stream_entry."""
        for writer in self._writers:
            try:
                writer.write(stream_entry)
            except WriterError as err:
                self._log.error("Error in writer: ", err, repr(stream_entry.entry))
                stream_entry.errors.append(f"{writer.__class__.__name__}: {str(err)}")
            except Exception as err:
                self._log.error(
                    "Unexpected error in writer: ", err, repr(stream_entry.entry)
                )
                stream_entry.errors.append(f"{writer.__class__.__name__}: {str(err)}")

        return stream_entry

    def read_entries(self, *args, **kwargs):
        """The total of entries obtained from the origin."""
        return self._read

    def written_entries(self, *args, **kwargs):
        """The total of entries written to destination."""
        return self._written

    def filtered_entries(self, *args, **kwargs):
        """The total of entries filtered out."""
        return self._filtered
