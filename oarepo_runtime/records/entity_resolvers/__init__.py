from oarepo import __version__ as oarepo_version

from oarepo_runtime.records.entity_resolvers.proxies import DraftProxy

# compatibility setting between invenio rdm 11 and invenio rdm 12
# can be removed when invenio rdm 11 is no longer supported
if oarepo_version.split(".")[0] == "11":
    from invenio_records_resources.references import EntityResolver, RecordResolver
    from invenio_users_resources.resolvers import UserResolver

    #copyied from newer invenio_users_resources, GroupResolver isn't in older versions
    from flask_principal import RoleNeed
    from invenio_accounts.models import Role
    from invenio_records_resources.references.resolvers import (
        EntityProxy,
        EntityResolver,
    )
    from invenio_users_resources.services.groups.config import GroupsServiceConfig
    from sqlalchemy.exc import NoResultFound

    class GroupProxy(EntityProxy):
        """Resolver proxy for a Role entity."""

        def _resolve(self):
            """Resolve the User from the proxy's reference dict, or system_identity."""
            # Resolves to role name, not id
            role_id = self._parse_ref_dict_id()
            try:
                return Role.query.filter(
                    Role.name == role_id  # TODO to be changed to role id
                ).one()
            except NoResultFound:
                return {}

        def pick_resolved_fields(self, identity, resolved_dict):
            """Select which fields to return when resolving the reference."""
            serialized_role = {}

            return serialized_role

        def get_needs(self, ctx=None):
            """Return needs based on the given roles."""
            role_id = self._parse_ref_dict_id()
            return [RoleNeed(role_id)]

        def ghost_record(self, value):
            """Return default representation of not resolved group.

            .. note::

                Only groups that are not indexed should need this. Non-indexed groups include groups that were not created by users
                e.g. user-moderation.
            """
            return {}


    class GroupResolver(EntityResolver):
        """Group entity resolver."""

        type_id = "group"
        """Type identifier for this resolver."""

        def __init__(self):
            """Constructor."""
            # There's a bit of a mixup of type_key and type_id. Base resolver has no
            # type_key, but RecordResolvers have.
            self.type_key = self.type_id
            super().__init__(GroupsServiceConfig.service_id)

        def matches_reference_dict(self, ref_dict):
            """Check if the reference dict references a role."""
            return self._parse_ref_dict_type(ref_dict) == self.type_id

        def _reference_entity(self, entity):
            """Create a reference dict for the given user."""
            return {"group": str(entity.id)}

        def matches_entity(self, entity):
            """Check if the entity is a Role."""
            return isinstance(entity, Role)

        def _get_entity_proxy(self, ref_dict):
            """Return a GroupProxy for the given reference dict."""
            return GroupProxy(self, ref_dict)

else:
    from invenio_records_resources.references import EntityResolver, RecordResolver
    from invenio_users_resources.entity_resolvers import UserResolver, GroupResolver

__all__ = ["DraftProxy", "UserResolver", "GroupResolver", "RecordResolver", "EntityResolver"]
