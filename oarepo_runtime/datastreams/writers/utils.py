import contextlib

from invenio_records.systemfields.relations.errors import InvalidRelationValue
from marshmallow import ValidationError

from oarepo_runtime.datastreams import StreamEntry

from ..types import StreamEntry, StreamEntryError
from .validation_errors import format_validation_error


@contextlib.contextmanager
def record_invenio_exceptions(stream_entry: StreamEntry):
    try:
        yield
    except ValidationError as err:
        validation_errors = format_validation_error(err.messages)
        for err_path, err_value in validation_errors.items():
            stream_entry.errors.append(
                StreamEntryError(
                    code="MARHSMALLOW", message=err_value, location=err_path
                )
            )
    except InvalidRelationValue as err:
        # TODO: better formatting for this kind of error
        stream_entry.errors.append(
            StreamEntryError.from_exception(err, message=err.args[0])
        )
    except Exception as err:
        stream_entry.errors.append(StreamEntryError.from_exception(err))
