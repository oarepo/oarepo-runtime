from invenio_access.permissions import system_identity
from invenio_pidstore.errors import PIDAlreadyExists
from invenio_records.systemfields.relations.errors import InvalidRelationValue
from invenio_records_resources.proxies import current_service_registry
from marshmallow import ValidationError

from ..errors import WriterError
from . import BaseWriter, StreamEntry


class ServiceWriter(BaseWriter):
    """Writes the entries to a repository instance using a Service object."""

    def __init__(self, *, service, identity=None, update=False, **kwargs):
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

    def _entry_id(self, entry):
        """Get the id from an entry."""
        return entry["id"]

    def _resolve(self, id_):
        return self._service.read(self._identity, id_)

    def write(self, stream_entry: StreamEntry, *args, uow=None, **kwargs):
        """Writes the input entry using a given service."""
        entry = stream_entry.entry
        service_kwargs = {}
        if uow:
            service_kwargs["uow"] = uow
        try:
            try:
                return self._service.create(self._identity, entry, **service_kwargs)
            except PIDAlreadyExists:
                if not self._update:
                    raise WriterError([f"Entry already exists: {entry}"])
                entry_id = self._entry_id(entry)
                current = self._resolve(entry_id)
                updated = dict(current.to_dict(), **entry)
                return self._service.update(
                    self._identity, entry_id, updated, **service_kwargs
                )

        except ValidationError as err:
            raise WriterError([{"ValidationError": err.messages}])
        except InvalidRelationValue as err:
            # TODO: Check if we can get the error message easier
            raise WriterError([{"InvalidRelationValue": err.args[0]}])

    def delete(self, stream_entry: StreamEntry, uow=None):
        service_kwargs = {}
        if uow:
            service_kwargs["uow"] = uow
        entry = stream_entry.entry
        self._service.delete(self._identity, entry["id"], **service_kwargs)
