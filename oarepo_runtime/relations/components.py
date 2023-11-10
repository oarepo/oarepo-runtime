import warnings

from oarepo_runtime.services.relations.components import CachingRelationsComponent

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.relations.components.CachingRelationsComponent",
    DeprecationWarning,
)

__all__ = ("CachingRelationsComponent",)
