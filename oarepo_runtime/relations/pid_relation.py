import warnings

from oarepo_runtime.records.relations.pid_relation import (
    PIDRelation,
    PIDRelationResult,
    MetadataPIDRelation,
    MetadataRelationResult,
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
