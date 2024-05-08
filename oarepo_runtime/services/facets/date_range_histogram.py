from invenio_search.engine import dsl
from invenio_records_resources.services.records.facets.facets import LabelledFacetMixin
from datetime import datetime, timedelta


class AutoDateHistogram(dsl.DateHistogramFacet):
    agg_type = "auto_date_histogram"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # def get_value(self, bucket):
    #     if not isinstance(bucket["key"], datetime):
    #         # OpenSearch returns key=None instead of 0 for date 1970-01-01,
    #         # so we need to set key to 0 to avoid TypeError exception
    #         if bucket["key"] is None:
    #             bucket["key"] = 0
    #         # Preserve milliseconds in the datetime
    #         return datetime.utcfromtimestamp(int(bucket["key"]) / 1000.0)
    #     else:
    #         return bucket["key"]

    def get_value_filter(self, filter_value):
        if "/" in filter_value:
            start, end = filter_value.split("/")
            return dsl.query.Range(
                _expand__to_dot=False,
                **{
                    self._params["field"]: {
                        "gte": start,
                        "lte": end,
                    }
                },
            )
        return super().get_value_filter(filter_value)


class DateRangeHistogram(LabelledFacetMixin, AutoDateHistogram):
    pass
