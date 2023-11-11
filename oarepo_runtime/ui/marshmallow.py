import warnings

from oarepo_runtime.services.schema.ui import (
    FormatTimeString,
    InvenioUISchema,
    LocalizedDate,
    LocalizedDateTime,
    LocalizedEDTF,
    LocalizedEDTFInterval,
    LocalizedEnum,
    LocalizedMixin,
    LocalizedTime,
    MultilayerFormatEDTF,
    PrefixedGettextField,
)

warnings.warn(
    "Deprecated, please use oarepo_runtime.services.schema.ui",
    DeprecationWarning,
)

__all__ = (
    "InvenioUISchema",
    "LocalizedEnum",
    "PrefixedGettextField",
    "LocalizedEDTFInterval",
    "LocalizedEDTF",
    "LocalizedTime",
    "LocalizedDateTime",
    "MultilayerFormatEDTF",
    "FormatTimeString",
    "LocalizedDate",
    "LocalizedMixin",
)
