from base64 import b64decode

import requests
from deprecated import deprecated
from flask import current_app
from invenio_drafts_resources.services import RecordService as DraftRecordService
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services import FileService, RecordService
from invenio_records_resources.services.records.results import RecordItem
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter


def get_record_service_for_record(record):
    if not record:
        return None
    if "OAREPO_PRIMARY_RECORD_SERVICE" in current_app.config:
        return get_record_service_for_record_class(type(record))
    else:
        return get_record_service_for_record_deprecated(record)


def get_record_service_for_record_class(record_cls):
    service_id = current_app.config["OAREPO_PRIMARY_RECORD_SERVICE"][record_cls]
    return current_service_registry.get(service_id)


@deprecated(
    version="1.5.43", reason="Please recompile model to remove this deprecation warning"
)
def get_record_service_for_record_deprecated(record):
    if getattr(record, "is_draft", False):
        record_name = "draft_cls"
        expect_draft_service = True
    else:
        record_name = "record_cls"
        expect_draft_service = False

    for svc in current_service_registry._services.values():
        if not isinstance(svc, RecordService):
            continue
        if isinstance(svc, FileService):
            continue
        is_draft_service = isinstance(svc, DraftRecordService)
        if is_draft_service != expect_draft_service:
            continue
        service_record = getattr(svc, record_name, None)
        if service_record == type(record):
            return svc

def get_file_service_for_record_class(record_class):
    if not record_class:
        return None

    for svc in current_service_registry._services.values():
        if not isinstance(svc, FileService):
            continue
        if svc.record_cls != record_class:
            continue
        return svc

def get_file_service_for_file_record_class(file_record_class):
    record_class = file_record_class.record_cls
    return get_file_service_for_record_class(record_class)

def get_file_service_for_record_service(
    record_service, check_draft_files=True, record=None
):
    if isinstance(record, RecordItem):
        record = record._record
    if record and getattr(record, "is_draft", False) is False:
        check_draft_files = False
    if (
        check_draft_files
        and hasattr(record_service, "draft_files")
        and isinstance(record_service.draft_files, FileService)
    ):
        return record_service.draft_files
    if hasattr(record_service, "files") and isinstance(
        record_service.files, FileService
    ):
        return record_service.files
    return get_file_service_for_record_class(
        getattr(record_service.config, "record_cls", None)
    )


def get_record_service_for_file_service(file_service, record=None):
    if record and getattr(record, "is_draft", False):
        record_name = "draft_cls"
        expect_draft_service = True
    else:
        record_name = "record_cls"
        expect_draft_service = False
    for svc in current_service_registry._services.values():
        if not isinstance(svc, RecordService):
            continue
        is_draft_service = isinstance(svc, DraftRecordService)
        if is_draft_service != expect_draft_service:
            continue
        service_record = getattr(svc, record_name, None)
        if service_record == file_service.record_cls:
            return svc

    raise KeyError(
        f"Could not get service for file service {file_service}, draft {expect_draft_service}"
    )


class DataAdapter(BaseAdapter):
    def send(
        self,
        request: PreparedRequest,
        stream=False,
        timeout=None,
        verify=True,
        cert=None,
        proxies=None,
    ):
        data = request.url.replace("data:", "")
        resp = Response()
        resp.status_code = 200
        resp._content = b64decode(data)
        return resp

    def close(self):
        pass


attachments_requests = requests.Session()
attachments_requests.mount("data:", DataAdapter())
