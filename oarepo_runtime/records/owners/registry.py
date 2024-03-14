from invenio_records_resources.references.registry import ResolverRegistryBase

from oarepo_runtime.proxies import current_oarepo


class OwnerEntityResolverRegistry(ResolverRegistryBase):
    """Entity Resolver registry for owners."""

    @classmethod
    def get_registered_resolvers(cls):
        """Get all currently registered resolvers."""
        return iter(current_oarepo.owner_entity_resolvers)

    @classmethod
    def resolve_reference(cls, reference):
        for resolver in cls.get_registered_resolvers():
            try:
                if resolver.matches_reference_dict(reference):
                    return resolver.get_entity_proxy(reference).resolve()
            except ValueError:
                # Value error ignored from matches_reference_dict
                pass
