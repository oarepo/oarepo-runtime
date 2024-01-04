import inspect

from invenio_records_resources.services.records.results import (
    RecordItem as BaseRecordItem,
)
from invenio_records_resources.services.records.results import (
    RecordList as BaseRecordList,
)


class AdditonalDataProcessingMixin:
    def _additional_processing(self, projection, record, *args, **kwargs):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, method in methods:
            if name.startswith("_process_"):
                method(projection, record, *args, **kwargs)


class RecordItem(BaseRecordItem, AdditonalDataProcessingMixin):
    """Single record result."""

    @property
    def data(self):
        if self._data:
            return self._data
        ret_data = super().data
        self._additional_processing(ret_data, self._record)
        return ret_data


class RecordList(BaseRecordList, AdditonalDataProcessingMixin):
    def _additional_processing(self, projection, record, *args, **kwargs):
        methods = inspect.getmembers(self, predicate=inspect.ismethod)
        for name, method in methods:
            if name.startswith("_process_"):
                method(projection, record, *args, **kwargs)

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
            self._additional_processing(projection, record)
            yield projection
