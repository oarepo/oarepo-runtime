import warnings

from oarepo_runtime.services.relations.mapping import RelationsMapping

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.relations.mapping.RelationsMapping",
    DeprecationWarning,
)

__all__ = ("RelationsMapping",)
