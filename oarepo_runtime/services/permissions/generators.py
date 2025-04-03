from typing import Literal

from flask import current_app
from flask_principal import RoleNeed, UserNeed
from invenio_records_permissions.generators import (
    ConditionalGenerator,
    Disable,
    Generator,
)
from invenio_search.engine import dsl


class RecordOwners(Generator):
    """Allows record owners."""

    def needs(self, record=None, **kwargs):
        """Enabling Needs."""
        if record is None:
            # 'record' is required, so if not passed we default to empty array,
            # i.e. superuser-access.
            return []
        if current_app.config.get("INVENIO_RDM_ENABLED", False):
            owners = getattr(record.parent.access, "owned_by", None)
            if owners is not None:
                owners_list = owners if isinstance(owners, list) else [owners]
                return [UserNeed(owner.owner_id) for owner in owners_list]
        else:
            owners = getattr(record.parent, "owners", None)
            if owners is not None:
                return [UserNeed(owner.id) for owner in owners]
        return []

    def query_filter(self, identity=None, **kwargs):
        """Filters for current identity as owner."""
        users = [n.value for n in identity.provides if n.method == "id"]
        if users:
            if current_app.config.get("INVENIO_RDM_ENABLED", False):
                return dsl.Q("terms", **{"parent.access.owned_by.user": users})
            else:
                return dsl.Q("terms", **{"parent.owners.user": users})
        return dsl.Q("match_none")


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


class IfDraftType(ConditionalGenerator):
    def __init__(
        self,
        draft_types: (
            list[Literal["initial"] | Literal["metadata"] | Literal["new_version"]]
            | Literal["initial"]
            | Literal["metadata"]
            | Literal["new_version"]
        ),
        then_=None,
        else_=None,
    ):
        if not isinstance(draft_types, (list, tuple)):
            draft_types = [draft_types]
        self._draft_types = draft_types
        if not then_:
            then_ = [Disable()]
        if not else_:
            else_ = [Disable()]
        if not isinstance(then_, (list, tuple)):
            then_ = [then_]
        if not isinstance(else_, (list, tuple)):
            else_ = [else_]
        super().__init__(then_, else_)

    def _condition(self, record=None, **kwargs):
        if not record:
            return False

        index = record.versions.index
        is_latest = record.versions.is_latest
        is_draft = record.is_draft

        if not is_draft:
            return False

        if index == 1 and not is_latest:
            draft_type = "initial"
        elif index > 1 and not is_latest:
            draft_type = "new_version"
        else:
            draft_type = "metadata"

        return draft_type in self._draft_types
