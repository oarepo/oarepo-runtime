from flask import current_app
from invenio_records_resources.proxies import current_service_registry

def get_record_service_for_record(record):
    if not record:
        return None
    return get_record_service_for_record_class(type(record))

def get_record_service_for_record_class(record_cls):
    service_id = current_app.config["OAREPO_PRIMARY_RECORD_SERVICE"][record_cls]
    return current_service_registry.get(service_id)