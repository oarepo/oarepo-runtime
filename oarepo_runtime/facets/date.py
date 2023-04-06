from invenio_records_resources.services.records.facets import TermsFacet
from oarepo_runtime.ui.marshmallow import (
    LocalizedDate,
    LocalizedTime,
    LocalizedDateTime,
    LocalizedEDTF,
    LocalizedEDTFInterval,
)
import re


class LabelledValuesTermsFacet(TermsFacet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **{"value_labels": self.value_labels, **kwargs})

    def value_labels(self, values):
        return {val: val for val in values}


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


class EDTFIntervalFacet(LabelledValuesTermsFacet):
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
