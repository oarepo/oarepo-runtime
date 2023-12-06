from invenio_records_resources.services.uow import unit_of_work

from oarepo_runtime.datastreams.utils import get_record_service_for_file_service


class FeaturedFileServiceMixin:
    @unit_of_work()
    def commit_file(self, identity, id_, file_key, uow=None):
        super().commit_file(identity, id_, file_key, uow=uow)

        record = self._get_record(id_, identity, "read", file_key=file_key)
        record_service = get_record_service_for_file_service(self, record=record)
        indexer = record_service.indexer
        if indexer:
            indexer.index(record)
            indexer.refresh()
