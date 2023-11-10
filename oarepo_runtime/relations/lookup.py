import warnings

from oarepo_runtime.records.relations.lookup import (lookup_key, LookupResult)

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.relations.lookup",
    DeprecationWarning,
)

__all__ = ("lookup_key", "LookupResult")
