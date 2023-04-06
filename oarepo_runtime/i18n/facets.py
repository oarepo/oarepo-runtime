from invenio_records_resources.services.records.facets import TermsFacet
from oarepo_runtime.ui.marshmallow import (
    LocalizedDate,
    LocalizedTime,
    LocalizedDateTime,
    LocalizedEDTF,
    LocalizedEDTFInterval,
)


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
        return {val: LocalizedEDTF().format_value(val) for val in values}


class EDTFIntervalFacet(LabelledValuesTermsFacet):
    def value_labels(self, values):
        return {val: LocalizedEDTFInterval().format_value(val) for val in values}
