from flask_principal import UserNeed
from invenio_records_permissions.generators import Generator
from invenio_search.engine import dsl


class RecordOwners(Generator):
    """Allows record owners."""

    def needs(self, record=None, **kwargs):
        """Enabling Needs."""
        if record is None:
            # 'record' is required, so if not passed we default to empty array,
            # i.e. superuser-access.
            return []
        owners = getattr(record.parent, "owners", None)
        if owners is not None:
            return [UserNeed(owner.id) for owner in owners]
        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        users = [n.value for n in identity.provides if n.method == "id"]
        if users:
            return dsl.Q("terms", **{"parent.owners.user": users})
