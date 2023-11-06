import warnings

from oarepo_runtime.services.expansions.expandable_fields import (
    ReferencedRecordExpandableField,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.expansions.expandable_fields.ReferencedRecordExpandableField",
    DeprecationWarning,
)

__all__ = ("ReferencedRecordExpandableField",)
