from invenio_records_resources.services.records.facets import TermsFacet


class LabelledValuesTermsFacet(TermsFacet):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **{"value_labels": self.value_labels, **kwargs})

    def value_labels(self, values):
        return {val: val for val in values}
