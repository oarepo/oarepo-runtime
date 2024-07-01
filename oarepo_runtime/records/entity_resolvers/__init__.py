from invenio_records_resources.references import EntityResolver, RecordResolver
from invenio_users_resources.entity_resolvers import GroupResolver, UserResolver

from oarepo_runtime.records.entity_resolvers.proxies import DraftProxy, RecordProxy

__all__ = [
    "DraftProxy",
    "UserResolver",
    "GroupResolver",
    "RecordResolver",
    "EntityResolver",
    "RecordProxy",
]
