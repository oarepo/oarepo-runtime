import abc
from typing import Iterable

from invenio_records_resources.services.base.links import LinksTemplate
from invenio_records_resources.services.base.service import Service
from invenio_records_resources.services.records.schema import ServiceSchemaWrapper


class EntityService(Service):
    @property
    def links_item_tpl(self):
        """Item links template."""
        return LinksTemplate(
            self.config.links_item,
        )

    @property
    def schema(self):
        """Returns the data schema instance."""
        return ServiceSchemaWrapper(self, schema=self.config.schema)

    @abc.abstractmethod
    def read(self, identity, id_, **kwargs):
        raise NotImplementedError()

    @abc.abstractmethod
    def read_many(self, identity, ids: Iterable[str], fields=None, **kwargs):
        raise NotImplementedError()


class KeywordEntityService(EntityService):

    def read(self, identity, id_, **kwargs):
        result = {"keyword": self.config.keyword, "id": id_}
        return self.result_item(
            self, identity, record=result, links_tpl=self.links_item_tpl
        )

    def read_many(self, identity, ids: Iterable[str], fields=None, **kwargs):
        if not ids:
            return []
        results = [{"keyword": self.config.keyword, "id": id} for id in ids]
        return self.result_list(
            self,
            identity,
            results=results,
            links_item_tpl=self.links_item_tpl,
        )
