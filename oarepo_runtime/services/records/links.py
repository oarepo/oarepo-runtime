from invenio_records_resources.services.base.links import Link

def pagination_links_html(tpl: str)->dict[str, Link]:
    """Create pagination links (prev/selv/next) from the same template."""
    return {
        "prev_html": Link(
            tpl,
            when=lambda pagination, ctx: pagination.has_prev,
            vars=lambda pagination, vars: vars["args"].update(
                {"page": pagination.prev_page.page}
            ),
        ),
        "self_html": Link(tpl),
        "next_html": Link(
            tpl,
            when=lambda pagination, ctx: pagination.has_next,
            vars=lambda pagination, vars: vars["args"].update(
                {"page": pagination.next_page.page}
            ),
        ),
    }