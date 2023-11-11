import re

from invenio_records_resources.services.records.facets.facets import LabelledFacetMixin
from invenio_search.engine import dsl

from oarepo_runtime.services.schema.ui import (
    LocalizedDate,
    LocalizedDateTime,
    LocalizedEDTF,
    LocalizedEDTFInterval,
    LocalizedTime,
)

from .base import LabelledValuesTermsFacet


class DateFacet(LabelledValuesTermsFacet):
    def localized_value_labels(self, values, locale):
        return {val: LocalizedDate(locale=locale).format_value(val) for val in values}


class TimeFacet(LabelledValuesTermsFacet):
    def localized_value_labels(self, values, locale):
        return {val: LocalizedTime(locale=locale).format_value(val) for val in values}


class DateTimeFacet(LabelledValuesTermsFacet):
    def localized_value_labels(self, values, locale):
        return {
            val: LocalizedDateTime(locale=locale).format_value(val) for val in values
        }


class EDTFFacet(LabelledValuesTermsFacet):
    def localized_value_labels(self, values, locale):
        return {
            val: LocalizedEDTF(locale=locale).format_value(convert_to_edtf(val))
            for val in values
        }


class AutoDateHistogramFacet(dsl.DateHistogramFacet):
    agg_type = "auto_date_histogram"

    def __init__(self, **kwargs):
        # skip DateHistogramFacet constructor
        super(dsl.DateHistogramFacet, self).__init__(**kwargs)


class EDTFIntervalFacet(LabelledFacetMixin, AutoDateHistogramFacet):
    # auto_date_histogram
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def localized_value_labels(self, values, locale):
        return {
            val: LocalizedEDTFInterval(locale=locale).format_value(convert_to_edtf(val))
            for val in values
        }


class DateIntervalFacet(EDTFIntervalFacet):
    pass


def convert_to_edtf(val):
    if "/" in val:
        # interval
        return "/".join(convert_to_edtf(x) for x in val.split("/"))
    val = re.sub(r"T.*", "", val)  # replace T12:00:00.000Z with nothing
    print(val)
    return val
