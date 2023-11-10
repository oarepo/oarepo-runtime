import warnings

from oarepo_runtime.uow import CachingUnitOfWork

# moved to oarepo_runtime.uow, kept here for backward compatibility

warnings.warn(
    "Deprecated, please use oarepo_runtime.uow.CachingUnitOfWork",
    DeprecationWarning,
)

__all__ = ["CachingUnitOfWork"]
