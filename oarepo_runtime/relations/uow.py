from invenio_records_resources.services.uow import UnitOfWork


class CachingUnitOfWork(UnitOfWork):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}
