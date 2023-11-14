from base64 import b64decode

import requests
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services import FileService
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter


def get_file_service_for_record_class(record_class):
    if not record_class:
        return None

    for svc in current_service_registry._services.values():
        if not isinstance(svc, FileService):
            continue
        if svc.record_cls != record_class:
            continue
        return svc


def get_file_service_for_record_service(record_service, check_draft_files=True, record=None):
    if record and getattr(record, 'is_draft', False):
        check_draft_files = False
    if check_draft_files and hasattr(record_service, "draft_files") and isinstance(record_service.draft_files, FileService):
        return record_service.draft_files
    if hasattr(record_service, "files") and isinstance(record_service.files, FileService):
        return record_service.files
    return get_file_service_for_record_class(getattr(record_service.config, "record_cls", None))


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
