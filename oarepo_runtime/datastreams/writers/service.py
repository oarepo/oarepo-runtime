from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.uow import UnitOfWork

from ...uow import BulkUnitOfWork
from ..types import StreamBatch, StreamEntry, StreamEntryError
from . import BaseWriter
from .utils import record_invenio_exceptions


class ServiceWriter(BaseWriter):
    """Writes the entries to a repository instance using a Service object."""

    def __init__(
        self,
        *,
        service,
        identity=None,
        update=False,
        **kwargs,
    ):
        """Constructor.
        :param service_or_name: a service instance or a key of the
                                service registry.
        :param identity: access identity.
        :param update: if True it will update records if they exist.
        :param write_files: if True it will write files to the file service.
        :param uow: UnitOfWork fully qualified class name or class to use for the unit of work.
        """
        super().__init__(**kwargs)

        if isinstance(service, str):
            service = current_service_registry.get(service)

        self._service = service
        self._identity = identity or system_identity
        self._update = update

    def _resolve(self, id_):
        if hasattr(self._service, "read_draft"):
            try:
                # try to read the draft first
                return self._service.read_draft(self._identity, id_)
            except PIDDoesNotExistError:
                pass
            try:
                # if the draft does not exist, read the published record
                # and create a draft for it
                rec = self._service.read(self._identity, id_)
                return self._service.edit(self._identity, id_)
            except PIDDoesNotExistError:
                pass

        else:
            try:
                return self._service.read(self._identity, id_)
            except PIDDoesNotExistError:
                pass
        return None

    def _get_stream_entry_id(self, entry: StreamEntry):
        return entry.id

    def write(self, batch: StreamBatch):
        """Writes the input entry using the given service."""
        with BulkUnitOfWork() as uow:
            for entry in batch.entries:
                if entry.filtered or entry.errors:
                    continue
                with record_invenio_exceptions(entry):
                    if entry.deleted:
                        self._delete_entry(entry, uow=uow)
                    else:
                        self._write_entry(entry, uow)
            uow.commit()

        return batch

    def _write_entry(self, stream_entry: StreamEntry, uow: UnitOfWork):
        entry = stream_entry.entry
        service_kwargs = {}
        if uow:
            service_kwargs["uow"] = uow

        do_create = True
        repository_entry = None  # just to make linter happy

        entry_id = self._get_stream_entry_id(stream_entry)

        if entry_id:
            if self._update:
                repository_entry = self.try_update(entry_id, entry, **service_kwargs)
                if repository_entry:
                    do_create = False
            else:
                current = self._resolve(entry_id)
                if current:
                    do_create = False

        if do_create:
            repository_entry = self._service.create(
                self._identity, entry, **service_kwargs
            )

        if repository_entry:
            stream_entry.entry = repository_entry.data
            stream_entry.id = repository_entry.id

            stream_entry.context["revision_id"] = repository_entry._record.revision_id
            if repository_entry.errors:
                for err in repository_entry.errors:
                    field = err.get("field")
                    messages = err.get("messages")
                    for message in messages:
                        stream_entry.errors.append(
                            StreamEntryError(
                                code="validation", message=message, location=field
                            )
                        )

    def try_update(self, entry_id, entry, **service_kwargs):
        current = self._resolve(entry_id)
        if current:
            updated = dict(current.to_dict(), **entry)
            # might raise exception here but that's ok - we know that the entry
            # exists in db as it was _resolved
            if hasattr(self._service, "update_draft"):
                # try to update draft first
                return self._service.update_draft(
                    self._identity, entry_id, updated, **service_kwargs
                )
            else:
                return self._service.update(
                    self._identity, entry_id, updated, **service_kwargs
                )

    def _delete_entry(self, stream_entry: StreamEntry, uow=None):
        entry_id = self._get_stream_entry_id(stream_entry)
        if not entry_id:
            return
        service_kwargs = {}
        if uow:
            service_kwargs["uow"] = uow
        deletion_exceptions = []
        deletion_tries = 0

        # if the service has drafts, try to delete it first
        if hasattr(self._service, "delete_draft"):
            # delete draft
            deletion_tries += 1
            try:
                self._service.delete_draft(self._identity, entry_id, **service_kwargs)
            except Exception as e:
                deletion_exceptions.append(e)

        # delete the record if it was published
        deletion_tries += 1
        try:
            self._service.delete(self._identity, entry_id, **service_kwargs)
        except Exception as e:
            deletion_exceptions.append(e)

        if len(deletion_exceptions) == deletion_tries:
            # all deletion attempts failed
            raise deletion_exceptions[-1]
