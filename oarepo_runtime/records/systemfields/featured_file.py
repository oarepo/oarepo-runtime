from invenio_access.permissions import system_identity
from invenio_records.systemfields import SystemField
from invenio_records_resources.proxies import current_service_registry

from oarepo_runtime.datastreams.utils import get_file_service_for_record_service
from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin


class FeaturedFileFieldResult(MappingSystemFieldMixin):
    def __init__(self, record=None):
        super().__init__()
        self.record = record

    def search_dump(self, data):
        for service in current_service_registry._services:
            # get_file_service_for_record_service
            if getattr(
                current_service_registry._services[service], "record_cls"
            ) == type(self.record):
                file_service = get_file_service_for_record_service(
                    record_service=current_service_registry._services[service],
                    record=self.record,
                )  # par
                # if hasattr(current_service_registry._services[service], "_get_record") \
                #         and self.record == current_service_registry._services[service]._get_record(self.record["id"],
                #                                                                                    system_identity, "read"):
                #     files = current_service_registry._services[service].list_files(system_identity,
                #                                                                            self.record['id'])
                files = file_service.list_files(system_identity, self.record["id"])
                file_list = list(files.entries)
                # print("file_list: ",file_list)
                # print(files.to_dict())
                for file in file_list:
                    if (
                        file["metadata"]
                        and "featured" in file["metadata"]
                        and file["metadata"]["featured"]
                    ):
                        self.record.update({"metadata": {"featured": file}})
                        self.record.commit()


class FeaturedFileField(SystemField):
    def __init__(self, source_field):
        super(FeaturedFileField, self).__init__()

    def __get__(self, instance, owner):
        if instance is None:
            return None
        result = FeaturedFileFieldResult(record=instance)
        return result
