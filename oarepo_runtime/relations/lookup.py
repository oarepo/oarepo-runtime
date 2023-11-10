import warnings

from oarepo_runtime.records.relations.lookup import lookup_key

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.relations.lookup.lookup_key",
    DeprecationWarning,
)

__all__ = ("lookup_key",)
