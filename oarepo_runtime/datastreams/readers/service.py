from base64 import b64encode
from typing import List

from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry

from ..types import StreamEntryFile
from ..utils import get_file_service_for_record_class
from . import BaseReader, StreamEntry


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
        self._record_cls = getattr(self._service.config, "record_cls", None)

        if self._record_cls and load_files:
            # try to get file service
            self._file_service = get_file_service_for_record_class(self._record_cls)

    def __iter__(self):
        for idx, entry in enumerate(self._service.scan(self._identity)):
            files: List[StreamEntryFile] = []
            if self._file_service:
                for f in self._file_service.list_files(
                    self._identity, entry["id"]
                ).entries:
                    file_item = self._file_service.get_file_content(
                        self._identity, entry["id"], f["key"]
                    )
                    with file_item.open_stream("rb") as ff:
                        base64_content = b64encode(ff.read()).decode("ascii")
                        files.append(
                            StreamEntryFile(
                                metadata=f, content_url=f"data:{base64_content}"
                            )
                        )

            yield StreamEntry(entry, files=files)
