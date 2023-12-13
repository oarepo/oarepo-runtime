import dataclasses
import inspect
from typing import List

from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.records import (
    SearchOptions as InvenioSearchOptions,
)
from invenio_records_resources.services.records.params import (
    PaginationParam,
    QueryStrParam,
    SortParam,
)
from invenio_records_resources.services.records.queryparser import SuggestQueryParser

# TODO: integrate this to invenio_records_resources.services.records and remove SearchOptions class
from oarepo_runtime.i18n import lazy_gettext as _
from oarepo_runtime.records.systemfields.icu import ICUSuggestField

from .facets.params import GroupedFacetsParam

try:
    from invenio_i18n import get_locale
except ImportError:
    from invenio_i18n.babel import get_locale


class SearchOptions(InvenioSearchOptions):
    params_interpreters_cls = [
        QueryStrParam,
        PaginationParam,
        SortParam,
        GroupedFacetsParam,
    ]

    sort_options = {
        "title": dict(
            title=_("By Title"),
            fields=["metadata.title"],  # ES defaults to desc on `_score` field
        ),
        "bestmatch": dict(
            title=_("Best match"),
            fields=["_score"],  # ES defaults to desc on `_score` field
        ),
        "newest": dict(
            title=_("Newest"),
            fields=["-created"],
        ),
        "oldest": dict(
            title=_("Oldest"),
            fields=["created"],
        ),
    }


@dataclasses.dataclass
class SuggestField:
    field: str
    boost: int
    use_ngrams: bool = True
    boost_exact: float = 5
    boost_2gram: float = 1
    boost_3gram: float = 1
    boost_prefix: float = 1


class ICUSuggestParser:
    def __init__(
        self,
        record_cls_or_service_name,
        extra_fields: List[SuggestField] = None,
        default_fields: List[SuggestField] = None,
    ):
        self.record_cls_or_service_name = record_cls_or_service_name
        self.extra_fields = extra_fields or []
        self.default_fields = default_fields or []

    @property
    def record_cls(self):
        if not isinstance(self.record_cls_or_service_name, str):
            return self.record_cls_or_service_name
        return current_service_registry.get(
            self.record_cls_or_service_name
        ).config.record_cls

    def __get__(self, instance, owner):
        search_as_you_type_fields: List[SuggestField] = []
        locale = get_locale()
        if locale:
            language = locale.language

            for fld_name, fld in inspect.getmembers(
                self.record_cls, lambda x: isinstance(x, ICUSuggestField)
            ):
                search_as_you_type_fields.append(
                    SuggestField(f"{fld_name}.{language}.original", 2)
                )
                search_as_you_type_fields.append(
                    SuggestField(f"{fld_name}.{language}.no_accent", 1)
                )

        if not search_as_you_type_fields:
            search_as_you_type_fields.extend(self.default_fields)

        search_as_you_type_fields.extend(self.extra_fields)

        fields = []
        for fld in search_as_you_type_fields:
            fields.append(f"{fld.field}^{fld.boost * fld.boost_exact}")
            if fld.use_ngrams:
                fields.append(f"{fld.field}._2gram^{fld.boost * fld.boost_2gram}")
                fields.append(f"{fld.field}._3gram^{fld.boost * fld.boost_3gram}")
                fields.append(
                    f"{fld.field}._index_prefix^{fld.boost * fld.boost_prefix}"
                )

        return SuggestQueryParser.factory(
            fields=fields,
        )


@dataclasses.dataclass
class SortField:
    option_name: str = "title"
    icu_sort_field: str = "sort"
    title: str = _("By Title")


class ICUSortOptions:
    def __init__(self, record_cls_or_service_name, fields: List[SortField] = None):
        self.record_cls_or_service_name = record_cls_or_service_name
        self.fields = fields or [SortField()]

    @property
    def record_cls(self):
        if not isinstance(self.record_cls_or_service_name, str):
            return self.record_cls_or_service_name
        return current_service_registry.get(
            self.record_cls_or_service_name
        ).config.record_cls

    def __get__(self, instance, owner):
        if not inspect.isclass(owner):
            owner = type(owner)
        super_options = {}
        for mro in list(owner.mro())[1:]:
            if hasattr(mro, "sort_options"):
                super_options = mro.sort_options
                break

        ret = {
            **super_options,
            **getattr(owner, "extra_sort_options", {}),
        }

        # transform the sort options by the current language
        locale = get_locale()
        if not locale:
            return ret

        language = locale.language

        for sort_field in self.fields:
            icu_field = getattr(self.record_cls, sort_field.icu_sort_field)
            ret[sort_field.option_name] = {
                "title": sort_field.title,
                "fields": [f"{icu_field.key}.{language}"],
            }
        return ret


class I18nSearchOptions(SearchOptions):
    extra_sort_options = {}
    record_cls = None
