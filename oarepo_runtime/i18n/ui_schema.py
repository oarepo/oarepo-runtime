import warnings

from oarepo_runtime.services.schema.i18n_ui import (
    I18nStrLocalizedUIField,
    I18nStrUIField,
    MultilingualLocalizedUIField,
    MultilingualUIField,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.i18n_ui",
    DeprecationWarning,
)

__all__ = (
    "MultilingualUIField",
    "I18nStrUIField",
    "MultilingualLocalizedUIField",
    "I18nStrLocalizedUIField",
)
