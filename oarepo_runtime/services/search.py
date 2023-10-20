import dataclasses
from typing import Tuple, List

from invenio_records_resources.services.records import (
    SearchOptions as InvenioSearchOptions,
)

# TODO: integrate this to invenio_records_resources.services.records
from flask_babelex import lazy_gettext as _
from invenio_records_resources.services.records.queryparser import SuggestQueryParser
from sqlalchemy.util import classproperty
from flask import current_app

try:
    from invenio_i18n import get_locale
except ImportError:
    from invenio_i18n.babel import get_locale


class SearchOptions(InvenioSearchOptions):
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


class I18nSearchOptions(SearchOptions):
    SORT_CUSTOM_FIELD_NAME = None
    SUGGEST_CUSTOM_FIELD_NAME = None
    SUGGEST_SEARCH_AS_YOU_TYPE_FIELDS: Tuple[SuggestField] = (
        SuggestField("metadata.title", 1, use_ngrams=False),
        SuggestField("id", 1, use_ngrams=False),
    )
    extra_sort_options = {}

    @classproperty
    def sort_options(clz):
        ret = {**super().sort_options, **clz.extra_sort_options}
        if not clz.SORT_CUSTOM_FIELD_NAME:
            return ret

        # transform the sort options by the current language
        locale = get_locale()
        if not locale:
            return ret
        language = locale.language
        for cf in current_app.config[clz.SORT_CUSTOM_FIELD_NAME]:
            if cf.name == language:
                ret["title"]["fields"] = [f"sort.{cf.name}"]
                break
        return ret

    @classproperty
    def suggest_parser_cls(clz):
        search_as_you_type_fields: List[SuggestField] = []
        locale = get_locale()

        if clz.SUGGEST_CUSTOM_FIELD_NAME and locale:
            language = locale.language
            for cf in current_app.config[clz.SUGGEST_CUSTOM_FIELD_NAME]:
                if cf.name == language:
                    search_as_you_type_fields.append(
                        SuggestField(f"suggest.{language}.original", 2)
                    )
                    search_as_you_type_fields.append(
                        SuggestField(f"suggest.{language}.no_accent", 1)
                    )
        if not search_as_you_type_fields:
            search_as_you_type_fields = clz.SUGGEST_SEARCH_AS_YOU_TYPE_FIELDS  # noqa

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
