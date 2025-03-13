"""An extension to invenio RDM service that includes a search across all records
(published, draft and deleted).
without any filtering. Permission `can_read_all_records` and `search_all_records`
were added and must be used to filter the results so that no information is leaked.
"""

from invenio_rdm_records.services import RDMRecordService
from invenio_records_resources.services import LinksTemplate


class SearchAllRecordsService(RDMRecordService):
    def search_all_records(
        self,
        identity,
        params=None,
        search_preference=None,
        expand=False,
        extra_filter=None,
        **kwargs,
    ):
        """Search for drafts records matching the querystring."""
        self.require_permission(
            identity,
            "search_all_records",
            params=params,
            extra_filter=extra_filter,
            **kwargs,
        )
        # Prepare and execute the search
        params = params or {}

        search_opts = (
            getattr(self.config, "search_all", None) or self.config.search_drafts
        )

        search_result = self._search(
            "search_all",
            identity,
            params,
            search_preference,
            record_cls=self.draft_cls,
            search_opts=search_opts,
            extra_filter=extra_filter,
            permission_action="read_all_records",
            **kwargs,
        ).execute()

        return self.result_list(
            self,
            identity,
            search_result,
            params,
            links_tpl=LinksTemplate(
                getattr(self.config, "links_search_drafts")
                or self.config.links_search_drafts,
                context={"args": params},
            ),
            links_item_tpl=self.links_item_tpl,
            expandable_fields=self.expandable_fields,
            expand=expand,
        )
