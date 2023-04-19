import re

from invenio_records_resources.services.records.facets.facets import LabelledFacetMixin
from invenio_search.engine import dsl

from oarepo_runtime.ui.marshmallow import (
    LocalizedDate,
    LocalizedDateTime,
    LocalizedEDTF,
    LocalizedEDTFInterval,
    LocalizedTime,
)

from .base import LabelledValuesTermsFacet


class DateFacet(LabelledValuesTermsFacet):
    def value_labels(self, values):
        return {val: LocalizedDate().format_value(val) for val in values}


class TimeFacet(LabelledValuesTermsFacet):
    def value_labels(self, values):
        return {val: LocalizedTime().format_value(val) for val in values}


class DateTimeFacet(LabelledValuesTermsFacet):
    def value_labels(self, values):
        return {val: LocalizedDateTime().format_value(val) for val in values}


class EDTFFacet(LabelledValuesTermsFacet):
    def value_labels(self, values):
        return {
            val: LocalizedEDTF().format_value(convert_to_edtf(val)) for val in values
        }


class EDTFIntervalFacet(LabelledFacetMixin, dsl.DateHistogramFacet):
    # auto_date_histogram
    def __init__(self, *args, **kwargs):
        if "interval" not in kwargs:
            kwargs["interval"] = "year"
        super().__init__(*args, **kwargs)

    def value_labels(self, values):
        return {
            val: LocalizedEDTFInterval().format_value(convert_to_edtf(val))
            for val in values
        }


def convert_to_edtf(val):
    if "/" in val:
        # interval
        return "/".join(convert_to_edtf(x) for x in val.split("/"))
    val = re.sub(r"T.*", "", val)  # replace T12:00:00.000Z with nothing
    print(val)
    return val
