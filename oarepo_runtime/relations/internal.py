import warnings

from oarepo_runtime.records.relations.internal import InternalResult, InternalRelation

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.relations",
    DeprecationWarning,
)

__all__ = (
    "InternalResult",
    "InternalRelation",
)
