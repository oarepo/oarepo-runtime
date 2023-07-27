from base64 import b64decode
from io import BytesIO

from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records.systemfields.relations.errors import InvalidRelationValue
from invenio_records_resources.proxies import current_service_registry
from marshmallow import ValidationError

from ..datastreams import StreamEntryError
from . import BaseWriter, StreamEntry
from .validation_errors import format_validation_error
from ..utils import get_file_service_for_record_class


class ServiceWriter(BaseWriter):
    """Writes the entries to a repository instance using a Service object."""

    def __init__(self, *, service, identity=None, update=False, write_files=True, **kwargs):
        """Constructor.
        :param service_or_name: a service instance or a key of the
                                service registry.
        :param identity: access identity.
        :param update: if True it will update records if they exist.
        """
        super().__init__(**kwargs)

        if isinstance(service, str):
            service = current_service_registry.get(service)

        self._service = service
        self._identity = identity or system_identity
        self._update = update

        self._file_service = None
        self._record_cls = getattr(self._service.config, 'record_cls', None)

        if self._record_cls and write_files:
            # try to get file service
            self._file_service = get_file_service_for_record_class(self._record_cls)

    def _entry_id(self, entry):
        """Get the id from an entry."""
        return entry.get("id")

    def _resolve(self, id_):
        try:
            return self._service.read(self._identity, id_)
        except PIDDoesNotExistError:
            return None

    def write(self, stream_entry: StreamEntry, *args, uow=None, **kwargs):
        """Writes the input entry using a given service."""
        entry = stream_entry.entry
        service_kwargs = {}
        if uow:
            service_kwargs["uow"] = uow
        try:
            entry_id = self._entry_id(entry)
            if (
                entry_id
                and self._update
                and self.try_update(entry_id, stream_entry, **service_kwargs)
            ):
                # update was successful
                return

            entry = self._service.create(self._identity, entry, **service_kwargs)

            stream_entry.entry = entry.data

            stream_entry.context['pid'] = entry.id

            if self._file_service and stream_entry.context.get('files', []):
                # store the files with the metadata
                for f in stream_entry.context['files']:
                    self._file_service.init_files(self._identity, entry.id, [{"key": f['metadata']["key"]}], **service_kwargs)
                    metadata = f['metadata'].get('metadata', {})
                    if metadata:
                        self._file_service.update_file_metadata(self._identity, entry.id, metadata, **service_kwargs)
                    self._file_service.set_file_content(self._identity, entry.id, f['metadata']['key'],
                                                        BytesIO(b64decode(f['content'])), **service_kwargs)
                    self._file_service.commit_file(self._identity, entry.id, f['metadata']['key'], **service_kwargs)

        except ValidationError as err:
            stream_entry.errors.append(
                StreamEntryError.from_exception(
                    err, message=format_validation_error(err.messages)
                )
            )
        except InvalidRelationValue as err:
            stream_entry.errors.append(
                StreamEntryError.from_exception(err, message=err.args[0])
            )
        except Exception as err:
            stream_entry.errors.append(StreamEntryError.from_exception(err))

    def try_update(self, entry_id, stream_entry, **service_kwargs):
        if entry_id:
            current = self._resolve(entry_id)
            if current:
                updated = dict(current.to_dict(), **stream_entry.entry)
                # might raise exception here but that's ok - we know that the entry
                # exists in db as it was _resolved
                stream_entry.entry = self._service.update(
                    self._identity, entry_id, updated, **service_kwargs
                )
                return True
        return False

    def delete(self, stream_entry: StreamEntry, uow=None):
        service_kwargs = {}
        if uow:
            service_kwargs["uow"] = uow
        entry = stream_entry.entry
        self._service.delete(self._identity, entry["id"], **service_kwargs)
