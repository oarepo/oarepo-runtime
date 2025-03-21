from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry
from invenio_requests.proxies import (
    current_requests_service as current_invenio_requests_service,
)
from oarepo_requests.proxies import current_oarepo_requests_service

from oarepo_runtime.datastreams.types import StreamBatch, StreamEntry
from oarepo_runtime.datastreams.writers import BaseWriter
from oarepo_runtime.datastreams.writers.utils import record_invenio_exceptions


class PublishWriter(BaseWriter):
    def __init__(
        self, *, service, request_name="publish_draft", identity=None, **kwargs
    ):
        if isinstance(service, str):
            service = current_service_registry.get(service)

        self._service = service
        self._identity = identity or system_identity
        self._request_name = request_name

    def write(self, batch: StreamBatch) -> StreamBatch:
        for entry in batch.ok_entries:
            if entry.deleted:
                continue

            with record_invenio_exceptions(entry):
                self._write_entry(entry)

    def _write_entry(self, entry: StreamEntry):
        draft = self._service.read_draft(self._identity, entry.id)
        request = current_oarepo_requests_service.create(
            identity=self._identity,
            data=None,
            request_type=self._request_name,
            topic=draft._record,
        )

        submit_result = current_invenio_requests_service.execute_action(
            self._identity, request.id, "submit"
        )
        accept_result = current_invenio_requests_service.execute_action(
            self._identity, request.id, "accept"
        )

        self._service.read(self._identity, draft["id"])
