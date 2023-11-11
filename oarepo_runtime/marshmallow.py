import warnings

from oarepo_runtime.services.schema.marshmallow import BaseRecordSchema

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.marshmallow.BaseRecordSchema",
    DeprecationWarning,
)

__all__ = ("BaseRecordSchema",)
