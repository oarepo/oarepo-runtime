import warnings

from oarepo_runtime.services.schema.i18n import I18nStrField, MultilingualField

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.i18n",
    DeprecationWarning,
)

__all__ = ("MultilingualField", "I18nStrField")
