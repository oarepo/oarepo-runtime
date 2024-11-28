from invenio_records_resources.errors import _iter_errors_dict
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

    @property
    def errors(self):
        return postprocess_errors(self._errors)

    def to_dict(self):
        """Get a dictionary for the record."""
        res = self.data
        if self._errors:
            res["errors"] = self.errors
        return res


def postprocess_error_messages(field_path: str, messages: any):
    """Postprocess error messages, looking for those that were not correctly processed by marshmallow/invenio.

    """
    if not isinstance(messages, list):
        yield {"field": field_path, "messages": messages}
    else:
        str_messages = [ msg for msg in messages if isinstance(msg, str) ]
        non_str_messages = [ msg for msg in messages if not isinstance(msg, str) ]

        if str_messages:
            yield {"field": field_path, "messages": str_messages}
        else:
            for non_str_msg in non_str_messages:
                yield from _iter_errors_dict(non_str_msg, field_path)


def postprocess_errors(errors: list[dict]):
    """Postprocess errors."""
    converted_errors = []
    for error in errors:
        if error.get("messages"):
            converted_errors.extend(postprocess_error_messages(error["field"], error["messages"]))
        else:
            converted_errors.append(error)
    return converted_errors

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
            if hasattr(self._service.config, "links_search_item"):
                links_tpl = self._service.config.search_item_links_template(
                    self._service.config.links_search_item
                )
                projection["links"] = links_tpl.expand(self._identity, record)
            elif self._links_item_tpl:
                projection["links"] = self._links_item_tpl.expand(
                    self._identity, record
                )
            # todo optimization viz FieldsResolver
            for c in self.components:
                c.update_data(
                    identity=self._identity,
                    record=record,
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
