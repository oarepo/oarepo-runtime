import warnings

from oarepo_runtime.services.schema.i18n_validation import lang_code_validator

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.i18n_validation.lang_code_validator",
    DeprecationWarning,
)

__all__ = ("lang_code_validator",)
