import warnings

from oarepo_runtime.services.schema.ui import InvenioUISchema

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.ui.InvenioUISchema",
    DeprecationWarning,
)

__all__ = ("InvenioUISchema",)
