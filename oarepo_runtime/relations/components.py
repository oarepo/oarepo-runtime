from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_runtime.relations.uow import CachingUnitOfWork


class CachingRelationsComponent(ServiceComponent):
    def create(self, identity, *, record, **kwargs):
        """Create handler."""
        # skutecny jmeno relations atributu
        if isinstance(self.uow, CachingUnitOfWork) and hasattr(record, "relations"):
            record.relations.set_cache(self.uow.cache)

    def update(self, identity, *, record, **kwargs):
        """Update handler."""
        self.create(identity, record=record, **kwargs)
