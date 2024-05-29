from invenio_records_resources.services.records.results import (
    RecordItem as BaseRecordItem,
)
from invenio_records_resources.services.records.results import (
    RecordList as BaseRecordList,
)


class ResultsComponent:
    def update_data(self, identity, record, projection, expand):
        raise NotImplementedError


class RecordItem(BaseRecordItem):
    """Single record result."""

    components = []

    @property
    def data(self):
        if self._data:
            return self._data
        _data = super().data
        for c in self.components:
            c.update_data(
                identity=self._identity,
                record=self._record,
                projection=_data,
                expand=self._expand,
            )
        return _data


class RecordList(BaseRecordList):
    components = []

    @property
    def hits(self):
        """Iterator over the hits."""
        for hit in self._results:
            # Load dump
            hit_dict = hit.to_dict()
            if hit_dict.get("record_status") == "draft":
                record = self._service.draft_cls.loads(hit_dict)
            else:
                record = self._service.record_cls.loads(hit_dict)

            # Project the record
            projection = self._schema.dump(
                record,
                context=dict(
                    identity=self._identity,
                    record=record,
                ),
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(
                    self._identity, record
                )
            # todo optimization viz FieldsResolver
            for c in self.components:
                c.update_data(
                    identity=self._identity,
                    record=self._record,
                    projection=projection,
                    expand=self._expand,
                )
            yield projection
