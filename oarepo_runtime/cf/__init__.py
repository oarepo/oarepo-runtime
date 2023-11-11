import warnings

from oarepo_runtime.services.custom_fields import (
    CustomFields,
    CustomFieldsMixin,
    InlinedCustomFields,
    InlinedCustomFieldsSchemaMixin,
    InlinedUICustomFieldsSchemaMixin,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.custom_fields",
    DeprecationWarning,
)

__all__ = (
    "CustomFieldsMixin",
    "CustomFields",
    "InlinedCustomFields",
    "InlinedCustomFieldsSchemaMixin",
    "InlinedUICustomFieldsSchemaMixin",
)
