from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry

from . import BaseReader, StreamEntry


class ServiceReader(BaseReader):
    """Writes the entries to a repository instance using a Service object."""

    def __init__(self, *, service=None, identity=None, **kwargs):
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

    def __iter__(self):
        for entry in self._service.scan(self._identity):
            yield StreamEntry(entry)
