from flask import g
from flask_resources import (
    resource_requestctx,
    response_handler,
    route,
)
from invenio_rdm_records.resources import RDMRecordResource
from invenio_records_resources.resources.records.resource import (
    request_extra_args,
    request_search_args,
    request_view_args,
)
from invenio_records_resources.resources.records.utils import search_preference


class BaseRecordResource(RDMRecordResource):

    def create_url_rules(self):
        """Create the URL rules for the record resource."""

        def p(route):
            """Prefix a route with the URL prefix."""
            return f"{self.config.url_prefix}{route}"

        def s(route):
            """Suffix a route with the URL prefix."""
            return f"{route}{self.config.url_prefix}"

        routes = self.config.routes
        url_rules = super(RDMRecordResource, self).create_url_rules()
        url_rules += [
            route("DELETE", p(routes["delete-record"]), self.delete_record),
            route("POST", p(routes["restore-record"]), self.restore_record),
            route("POST", p(routes["set-record-quota"]), self.set_record_quota),
            # TODO: move to users?
            route("POST", routes["set-user-quota"], self.set_user_quota),
            route("GET", s(routes["all-prefix"]), self.search_all_records),
        ]

        return url_rules

    @request_extra_args
    @request_search_args
    @request_view_args
    @response_handler(many=True)
    def search_all_records(self):
        """Perform a search over all records. Permission generators for search_all_records
        and read_all_records must be in place and must be used to filter the results so that
        no information is leaked.

        GET /all/records
        """
        hits = self.service.search_all_records(
            identity=g.identity,
            params=resource_requestctx.args,
            search_preference=search_preference(),
            expand=resource_requestctx.args.get("expand", False),
        )
        return hits.to_dict(), 200
