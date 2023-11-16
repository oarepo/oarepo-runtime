from io import BytesIO

from invenio_access.permissions import system_identity
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.uow import UnitOfWork

from ...uow import BulkUnitOfWork
from ..types import StreamBatch, StreamEntry
from ..utils import attachments_requests, get_file_service_for_record_service
from . import BaseWriter
from .utils import record_invenio_exceptions


class AttachmentsServiceWriter(BaseWriter):
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

        self._identity = identity or system_identity
        self._update = update

        self._file_service = None
        self._record_cls = getattr(service.config, "record_cls", None)

        self._file_service = get_file_service_for_record_service(service)

    def _get_stream_entry_id(self, entry: StreamEntry):
        return entry.id

    def write(self, batch: StreamBatch):
        """Writes the input entry using the given service."""

        with BulkUnitOfWork() as uow:
            for entry in batch.entries:
                if not entry.ok or entry.deleted:
                    continue
                with record_invenio_exceptions(entry):
                    self._write_attachments(entry, uow)

            uow.commit()

        return batch

    def _write_attachments(self, stream_entry: StreamEntry, uow: UnitOfWork):
        service_kwargs = {}
        if uow:
            service_kwargs["uow"] = uow
        entry_id = self._get_stream_entry_id(stream_entry)

        existing_files = self._file_service.list_files(self._identity, entry_id)
        existing_files = {f["key"]: f for f in existing_files.entries}

        for f in stream_entry.files:
            if f.metadata["key"] in existing_files:
                if not self._update:
                    continue
                # TODO: compare if the file should be deleted and re-created
                # if so, delete the file and create again
                self._file_service.delete_file(
                    self._identity, entry_id, f.metadata["key"], **service_kwargs
                )

            self._file_service.init_files(
                self._identity,
                entry_id,
                [{"key": f.metadata["key"]}],
                **service_kwargs,
            )
            metadata = f.metadata.get("metadata", {})
            if metadata:
                self._file_service.update_file_metadata(
                    self._identity,
                    entry_id,
                    file_key=f.metadata["key"],
                    data=metadata,
                    **service_kwargs,
                )
            self._file_service.set_file_content(
                self._identity,
                entry_id,
                f.metadata["key"],
                BytesIO(attachments_requests.get(f.content_url).content),
                **service_kwargs,
            )
            self._file_service.commit_file(
                self._identity, entry_id, f.metadata["key"], **service_kwargs
            )
        new_files_keys = set(f.metadata["key"] for f in stream_entry.files)

        for existing_file_key in existing_files:
            if existing_file_key not in new_files_keys:
                self._file_service.delete_file(
                    self._identity, entry_id, existing_file_key, **service_kwargs
                )
