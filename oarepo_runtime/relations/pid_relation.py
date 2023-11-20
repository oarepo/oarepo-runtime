import warnings

from oarepo_runtime.records.relations.pid_relation import (
    MetadataPIDRelation,
    MetadataRelationResult,
    PIDRelation,
    PIDRelationResult,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.relations",
    DeprecationWarning,
)

__all__ = (
    "PIDRelation",
    "PIDRelationResult",
    "MetadataPIDRelation",
    "MetadataRelationResult",
)
