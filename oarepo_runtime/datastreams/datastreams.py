#
# This package was taken from Invenio vocabularies and modified to be more universal
#
import itertools

from .errors import TransformerError, WriterError


class StreamEntry:
    """Object to encapsulate streams processing."""

    def __init__(self, entry, errors=None):
        """Constructor."""
        self.entry = entry
        self.filtered = False
        self.errors = errors or []


class DataStream:
    """Data stream."""

    def __init__(self, readers, writers, transformers=None, *args, **kwargs):
        """Constructor.
        :param readers: an ordered list of readers.
        :param writers: an ordered list of writers.
        :param transformers: an ordered list of transformers to apply.
        """
        self._readers = readers
        self._transformers = transformers
        self._writers = writers
        self._read = 0
        self._filtered = 0
        self._written = 0

    def process(self, *args, **kwargs):
        """Iterates over the entries.
        Uses the reader to get the raw entries and transforms them.
        It will iterate over the `StreamEntry` objects returned by
        the reader, apply the transformations and yield the result of
        writing it.
        """
        for stream_entry in self.read():
            self._read += 1
            if stream_entry.errors:
                yield stream_entry  # reading errors
            else:
                transformed_entry = self.transform(stream_entry)
                if transformed_entry.errors:
                    yield transformed_entry
                elif transformed_entry.filtered:
                    self._filtered += 1
                    yield transformed_entry
                else:
                    yield self.write(transformed_entry)
                    self._written += 1

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
