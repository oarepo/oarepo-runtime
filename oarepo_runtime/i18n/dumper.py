import warnings

from oarepo_runtime.records.dumpers.multilingual_dumper import MultilingualDumper

warnings.warn(
    "Deprecated, please use oarepo_runtime.records.dumpers.multilingual_dumper.MultilingualDumper",
    DeprecationWarning,
)

__all__ = ("MultilingualDumper",)
