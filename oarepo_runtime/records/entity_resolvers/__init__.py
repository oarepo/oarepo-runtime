from oarepo_runtime.records.entity_resolvers.proxies import DraftProxy, RecordProxy

from invenio_records_resources.references import EntityResolver, RecordResolver
from invenio_users_resources.entity_resolvers import UserResolver, GroupResolver

__all__ = ["DraftProxy", "UserResolver", "GroupResolver", "RecordResolver", "EntityResolver", "RecordProxy"]
