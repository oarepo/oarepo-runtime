import copy
import logging
from typing import List

from flask import current_app
from flask_principal import Identity
from invenio_access.permissions import system_user_id
from invenio_app.helpers import obj_or_import_string
from invenio_records_resources.services.records.facets import FacetsResponse
from invenio_records_resources.services.records.params import FacetsParam

log = logging.getLogger(__name__)


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
    def __init__(self, config):
        super().__init__(config)
        self._facets = {**config.facets}

    @property
    def facets(self):
        return self._facets

    def identity_facet_groups(self, identity: Identity) -> List[str]:
        if "OAREPO_FACET_GROUP_NAME" in current_app.config:
            find_facet_groups_func = obj_or_import_string(
                current_app.config["OAREPO_FACET_GROUP_NAME"]
            )
            return find_facet_groups_func(identity, self.config, None)

        if hasattr(identity, "provides"):
            return [need.value for need in identity.provides if need.method == "role"]

        return []

    @property
    def facet_groups(self):
        if hasattr(self.config, "facet_groups"):
            return self.config.facet_groups
        return None

    def identity_facets(self, identity: Identity):
        if not self.facet_groups:
            log.warning(
                "No facet groups defined on the service config %s", type(self.config)
            )
            return self.facets

        has_system_user_id = identity.id == system_user_id
        has_system_process_need = any(
            need.method == "system_process" for need in identity.provides
        )
        if has_system_user_id or has_system_process_need:
            return self.facets

        user_facets = self._filter_user_facets(identity)
        return user_facets

    def aggregate(self, search, user_facets):
        for name, facet in user_facets.items():
            agg = facet.get_aggregation()
            search.aggs.bucket(name, agg)

        return search

    def apply(self, identity, search, params):
        """Evaluate the facets on the search."""
        facets_values = params.pop("facets", {})
        for name, values in facets_values.items():
            if name in self.facets:
                self.add_filter(name, values)

        user_facets = self.identity_facets(identity)
        self_copy = copy.copy(self)
        self_copy._facets = user_facets
        search = search.response_class(FacetsResponse.create_response_cls(self_copy))

        search = self.aggregate(search, user_facets)
        search = self.filter(search)

        params.update(self.selected_values)

        return search

    def _filter_user_facets(self, identity: Identity):
        user_facets = {}
        if not self.facet_groups:
            user_facets.update(self.facets)
        else:
            self.facets.clear()  # TODO: why is this needed?
            user_facets.update(self.facet_groups.get("default", {}))

        groups = self.identity_facet_groups(identity)
        for group in groups:
            user_facets.update(self.facet_groups.get(group, {}))
        return user_facets
