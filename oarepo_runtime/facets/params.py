from flask import current_app
from flask_principal import Identity
from invenio_app.helpers import obj_or_import_string
from invenio_records_resources.services.records.params import FacetsParam
from invenio_records_resources.services.records.facets import FacetsResponse

from typing import List

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

class GroupedFacetsParam(FacetsParam):
    def identity_facet_groups(self, identity: Identity) -> List[str]:
        if "OAREPO_FACET_GROUP_NAME" in current_app.config:
            find_facet_groups_func = obj_or_import_string(current_app.config["OAREPO_FACET_GROUP_NAME"])
            if groups_names := find_facet_groups_func(identity, self.config, None):
                return groups_names
        else:
            if hasattr(identity, "provides"):
                return [need.value for need in identity.provides if need.method == "role"]
        
        return []

    def identity_facets(self, identity: Identity):
        user_facets = {}
        if "default" not in self.config.facet_groups:
            user_facets.update(self.facets)
        else:
            self.facets.clear()
            user_facets.update(self.config.facet_groups["default"])
        
        groups = self.identity_facet_groups(identity)
        for group in groups:
            user_facets.update(self.config.facet_groups.get(group, {}))
        
        self.facets.update(user_facets)

    def apply(self, identity, search, params):
        """Evaluate the facets on the search."""
        facets_values = params.pop("facets", {})
        for name, values in facets_values.items():
            if name in self.facets:
                self.add_filter(name, values)

        search = search.response_class(FacetsResponse.create_response_cls(self))

        self.identity_facets(identity)
        search = self.aggregate(search)
        search = self.filter(search)

        params.update(self.selected_values)

        return search