import warnings

from oarepo_runtime.records.relations.lookup import LookupResult, lookup_key

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.relations.lookup",
    DeprecationWarning,
)

__all__ = ("lookup_key", "LookupResult")
