from invenio_records_resources.services.base.links import Link
from oarepo_runtime.services.config import has_permission

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

class PermissionRequiringLink(Link):
    def __init__(self, link: Link, permission: str):
        """Constructor."""
        self._permission = has_permission(permission)
        self._link = link

    def should_render(self, obj, ctx):
        """Determine if the link should be rendered."""
        if self._permission(obj, ctx):
            return self._link.should_render(obj, ctx)
        return False

    def expand(self, obj, context):
        """Expand the URI Template."""
        return self._link.expand(obj, context)