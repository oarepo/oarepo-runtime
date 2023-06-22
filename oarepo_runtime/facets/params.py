from invenio_records_resources.services.records.params import FacetsParam


class FilteredFacetsParam(FacetsParam):
    def filter(self, search):
        """Apply a post filter on the search."""
        if not self._filters:
            return search

        filters = list(self._filters.values())

        facet_filter = filters[0]
        for f in filters[1:]:
            facet_filter &= f

        return search.filter(facet_filter)
