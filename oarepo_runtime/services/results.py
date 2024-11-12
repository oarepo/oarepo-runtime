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
    def aggregations(self):
        """Get the search result aggregations."""
        try:
            result = super().aggregations
            if result is None:
                return result

            for key in result.keys():
                if "buckets" in result[key]:
                    for bucket in result[key]["buckets"]:
                        val = bucket["key"]
                        label = bucket.get("label", "")

                        if not isinstance(val, str):
                            bucket["key"] = str(val)
                        if not isinstance(label, str):
                            bucket["label"] = str(label)
            return result
        except AttributeError:
            return None

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


class ArrayRecordItem(RecordItem):
    """Single record result."""

    @property
    def id(self):
        """Get the record id."""
        return self._record["id"]


class ArrayRecordList(RecordList):
    # move to runtime

    @property
    def total(self):
        """Get total number of hits."""
        return len(self._results)

    @property
    def aggregations(self):
        """Get the search result aggregations."""
        return None

    @property
    def hits(self):
        """Iterator over the hits."""
        for hit in self._results:
            # Project the record
            projection = self._schema.dump(
                hit,
                context=dict(
                    identity=self._identity,
                    record=hit,
                ),
            )
            if self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(self._identity, hit)
            if self._nested_links_item:
                for link in self._nested_links_item:
                    link.expand(self._identity, hit, projection)

            for c in self.components:
                c.update_data(
                    identity=self._identity,
                    record=hit,
                    projection=projection,
                    expand=self._expand,
                )
            yield projection
