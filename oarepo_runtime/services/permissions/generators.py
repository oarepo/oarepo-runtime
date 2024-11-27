from flask_principal import RoleNeed, UserNeed
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
        owners = getattr(record.parent.access, "owned_by", None)
        if owners is not None:
            return [UserNeed(owner.id) for owner in owners]
        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        users = [n.value for n in identity.provides if n.method == "id"]
        if users:
            return dsl.Q("terms", **{"parent.access.owned_by.user": users})


class UserWithRole(Generator):
    def __init__(self, *roles):
        self.roles = roles

    def needs(self, **kwargs):
        return [RoleNeed(role) for role in self.roles]

    def query_filter(self, identity=None, **kwargs):
        if not identity:
            return dsl.Q("match_none")
        for provide in identity.provides:
            if provide.method == "role" and provide.value in self.roles:
                return dsl.Q("match_all")
        return dsl.Q("match_none")
