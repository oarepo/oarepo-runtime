import warnings

from oarepo_runtime.records.relations.base import (
    InvalidCheckValue,
    InvalidRelationValue,
    Relation,
    RelationResult,
    RelationsField,
)
from oarepo_runtime.records.relations.internal import InternalRelation
from oarepo_runtime.records.relations.pid_relation import PIDRelation

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
    "InternalRelation",
    "PIDRelation",
)
