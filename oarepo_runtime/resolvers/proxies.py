import warnings

from oarepo_runtime.records.resolvers.proxies import DraftProxy

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.resolvers.proxies.DraftProxy",
    DeprecationWarning,
)

__all__ = ("DraftProxy",)
