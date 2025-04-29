from invenio_records_resources.services.records.facets.facets import LabelledFacetMixin
from opensearch_dsl import Facet


class MinFacet(LabelledFacetMixin, Facet):
    agg_type = "min"

    def get_labelled_values(self, data, filter_values):
        value = None
        if "value_as_string" in data:
            value = data["value_as_string"]

        return {"label": str(self._label), "value": value}
