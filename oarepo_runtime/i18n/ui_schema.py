import warnings

from oarepo_runtime.services.schema.i18n_ui import (MultilingualUIField,
                                                    I18nStrUIField,
                                                    MultilingualLocalizedUIField,
                                                    I18nStrLocalizedUIField)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.i18n_ui",
    DeprecationWarning,
)

__all__ = ("MultilingualUIField",
           "I18nStrUIField",
           "MultilingualLocalizedUIField",
           "I18nStrLocalizedUIField")
