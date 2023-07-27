from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services import FileService


def get_file_service_for_record_class(record_class):
    for svc in current_service_registry._services.values():
        if not isinstance(svc, FileService):
            continue
        if svc.record_cls != record_class:
            continue
        return svc
