import copy
import logging
import operator
from functools import partial, reduce
from typing import List

from flask import current_app
from flask_principal import Identity
from invenio_access.permissions import system_user_id
from invenio_app.helpers import obj_or_import_string
from invenio_records_resources.services.records.facets import FacetsResponse
from invenio_records_resources.services.records.params import FacetsParam
from invenio_access.permissions import authenticated_user
from invenio_records_resources.services.records.params.base import ParamInterpreter
from invenio_search.engine import dsl
from invenio_rdm_records.records.systemfields.deletion_status import (
    RecordDeletionStatusEnum,
)

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
        global_search_model = False
        for model in current_app.config.get("GLOBAL_SEARCH_MODELS", []):
            service_config = obj_or_import_string(model["service_config"])
            if service_config == self.config:
                global_search_model = True

        if not self.facet_groups:
            if global_search_model:
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

    def filter(self, search):
        """Apply a post filter on the search."""
        if not self._filters:
            return search

        filters = list(self._filters.values())

        _filter = filters[0]
        for f in filters[1:]:
            _filter &= f

        return search.filter(_filter).post_filter(_filter)

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


class OARepoAllVersionsParam(ParamInterpreter):
    """Evaluates the 'allversions' parameter."""
    def __init__(self, field_names, config):
        """Construct."""
        self.field_names = field_names
        super().__init__(config)

    @classmethod
    def factory(cls, field_names: list[str]):
        """Create a new filter parameter."""
        return partial(cls, field_names)

    def apply(self, identity, search, params):
        """Evaluate the allversions parameter on the search."""
        if not params.get("allversions"):
            queries = [dsl.query.Q("term", **{field_name: True}) for field_name in self.field_names]
            query = reduce(operator.or_, queries)
            search = search.filter(query)
        return search

class OARepoPublishedRecordsParam(ParamInterpreter):
    """Evaluates the include_deleted parameter."""

    def apply(self, identity, search, params):
        """Evaluate the include_deleted parameter on the search."""

        value = params.pop("include_deleted", None)
        # Filter prevents from displaying deleted records on mainsite search
        # deleted records should appear only in admins panel
        if value is None:
            query = dsl.query.Q(
                "bool",
                should=[
                    dsl.query.Q(
                        "bool",
                        must=[
                            dsl.query.Q(
                                "term",
                                deletion_status=RecordDeletionStatusEnum.PUBLISHED.value,
                            )
                        ],
                    ),
                    # Drafts does not have deletion_status so this clause is needed to
                    # prevent the above clause from filtering out the drafts
                    dsl.query.Q(
                        "bool", must_not=[dsl.query.Q("exists", field="deletion_status")]
                    ),
                ],
            )
            search = search.filter(query)
        return search