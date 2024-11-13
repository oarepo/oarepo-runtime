from invenio_records_resources.services.base.config import ServiceConfig

from ..results import ArrayRecordItem, ArrayRecordList
from .schema import KeywordEntitySchema


class EntityServiceConfig(ServiceConfig):
    links_item = {}
    result_item_cls = ArrayRecordItem
    result_list_cls = ArrayRecordList


class KeywordEntityServiceConfig(EntityServiceConfig):
    schema = KeywordEntitySchema
