import warnings

from oarepo_runtime.records.relations.base import (
    InvalidCheckValue,
    InvalidRelationValue,
    Relation,
    RelationResult,
    RelationsField,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.relations",
    DeprecationWarning,
)

__all__ = (
    "Relation",
    "RelationResult",
    "InvalidRelationValue",
    "InvalidCheckValue",
    "RelationsField",
)
