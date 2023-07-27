from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services import FileService

from . import BaseReader, StreamEntry
from base64 import b64encode

from ..utils import get_file_service_for_record_class


class ServiceReader(BaseReader):
    """Writes the entries to a repository instance using a Service object."""

    def __init__(self, *, service=None, identity=None, load_files=False, **kwargs):
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
        self._file_service = None
        self._record_cls = getattr(self._service.config, 'record_cls', None)

        if self._record_cls and load_files:
            # try to get file service
            self._file_service = get_file_service_for_record_class(self._record_cls)

    def __iter__(self):
        for idx, entry in enumerate(self._service.scan(self._identity)):
            files = []
            if self._file_service:
                for f in self._file_service.list_files(self._identity, entry['id']).entries:
                    file_item = self._file_service.get_file_content(self._identity, entry['id'], f['key'])
                    with file_item.open_stream("rb") as ff:
                        file_rec = {
                            'metadata': f,
                            'content': b64encode(ff.read())
                        }
                    files.append(file_rec)

            yield StreamEntry(entry, context={
                'serial_no': idx+1,     # make serial number 1 based
                'files': files
            })
