import warnings

from oarepo_runtime.services.schema.i18n import (MultilingualField,
                                                 I18nStrField)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.i18n",
    DeprecationWarning,
)

__all__ = ("MultilingualField","I18nStrField")
