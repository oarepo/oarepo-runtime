from invenio_access.permissions import system_identity
from invenio_records.systemfields import SystemField
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime.datastreams.utils import get_file_service_for_record_service
from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin


class FeaturedFileFieldResult:
    def __init__(self, record=None):
        super().__init__()
        self.record = record


class FeaturedFileField(MappingSystemFieldMixin, SystemField):
    def __init__(self, source_field):
        super(FeaturedFileField, self).__init__(source_field)

    def __get__(self, instance, owner):
        if instance is None:
            return self
        result = FeaturedFileFieldResult(record=instance)
        return result

    def search_dump(self, data, record):
        for service in current_service_registry._services:
            if getattr(
                current_service_registry._services[service], "record_cls"
            ) == type(record):
                file_service = get_file_service_for_record_service(
                    record_service=current_service_registry._services[service],
                    record=record,
                )

                files = file_service.list_files(system_identity, record["id"])
                file_list = list(files.entries)

                for file in file_list:
                    if (
                        file["metadata"]
                        and "featured" in file["metadata"]
                        and file["metadata"]["featured"]
                    ):
                        record["metadata"].update({"featured": file})
                        record.commit()
