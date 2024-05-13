from invenio_search.engine import dsl
from invenio_records_resources.services.records.facets.facets import LabelledFacetMixin
from datetime import datetime
from dateutil.relativedelta import relativedelta


class AutoDateHistogram(dsl.DateHistogramFacet):
    agg_type = "auto_date_histogram"

    def __init__(self, **kwargs):
        self._min_doc_count = kwargs.pop("min_doc_count", 0)
        super(dsl.DateHistogramFacet, self).__init__(**kwargs)

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
    def turn_edtf_string_to_date(self, edtf_string):
        return datetime.strptime(edtf_string, "%Y-%m-%d").date()

    def get_last_date(self, end_date):
        if end_date >= datetime.now().date():
            return datetime.now().date().strftime("%Y-%m-%d")
        else:
            return end_date.strftime("%Y-%m-%d")

    def get_last_value(self, interval, start):
        if "y" in interval:
            interval = int(interval.replace("y", ""))
            end = self.turn_edtf_string_to_date(start) + relativedelta(years=interval)
            return self.get_last_date(end)
        elif "M" in interval:
            interval = int(interval.replace("M", ""))
            end = self.turn_edtf_string_to_date(start) + relativedelta(months=interval)
            return self.get_last_date(end)
        elif "d" in interval:
            interval = int(interval.replace("d", ""))
            end = self.turn_edtf_string_to_date(start) + relativedelta(days=interval)
            return self.get_last_date(end)

    def get_labelled_values(self, data, filter_values):
        """Get a labelled version of a bucket."""
        out = []
        interval = data.to_dict()["interval"]
        buckets = data.buckets
        if self._min_doc_count > 0:
            buckets = [
                bucket
                for bucket in data.buckets
                if bucket.doc_count >= self._min_doc_count
            ]

        # We get the labels first, so that we can efficiently query a resource
        # for all keys in one go, vs querying one by one if needed.
        for i, bucket in enumerate(buckets):
            start = self.get_value(bucket)
            if interval == "1d":
                out.append(
                    {
                        "start": start,
                        "end": start,
                        "doc_count": self.get_metric(bucket),
                    }
                )
            else:
                out.append(
                    {
                        "start": start,
                        "end": self.get_value(buckets[i + 1])
                        if i + 1 < len(buckets)
                        else self.get_last_value(interval, start),
                        "doc_count": self.get_metric(bucket),
                    }
                )
        return {
            "buckets": out,
            "label": str(self._label),
            "interval": interval,
        }
