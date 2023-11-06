from base64 import b64decode

import requests
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services import FileService
from requests import PreparedRequest, Response
from requests.adapters import BaseAdapter


def get_file_service_for_record_class(record_class):
    for svc in current_service_registry._services.values():
        if not isinstance(svc, FileService):
            continue
        if svc.record_cls != record_class:
            continue
        return svc


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
