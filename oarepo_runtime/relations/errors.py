import warnings

from oarepo_runtime.services.relations.errors import (
    InvalidRelationError,
    MultipleInvalidRelationErrors,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.relations.errors",
    DeprecationWarning,
)

__all__ = ("InvalidRelationError", "MultipleInvalidRelationErrors")
