from functools import cached_property
from typing import Dict

from flask import current_app
from invenio_records.systemfields import SystemField

from oarepo_runtime.records.relations.lookup import lookup_key
from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin


class ICUField(MappingSystemFieldMixin, SystemField):
    """
    A system field that acts as an opensearch "proxy" to another field.
    It creates a top-level mapping field with the same name and copies
    content of {another field}.language into {mapping field}.language.

    The language accessor can be modified by overriding get_values method.
    """

    def __init__(self, *, source_field, key=None):
        super().__init__(key)
        self.source_field = source_field

    @cached_property
    def languages(self) -> Dict[str, Dict]:
        icu_languages = current_app.config.get("OAREPO_ICU_LANGUAGES", {})
        if icu_languages:
            return icu_languages

        primary_language = current_app.config.get("BABEL_DEFAULT_LOCALE", "en")
        # list of tuples [lang, title], just take lang
        babel_languages = [x[0] for x in current_app.config.get("I18N_LANGUAGES", [])]

        return {primary_language: {}, **{k: {} for k in babel_languages}}

    def get_values(self, data, language):
        ret = []
        for l in lookup_key(data, f"{self.source_field}"):
            if isinstance(l.value, str):
                ret.append(l.value)
            elif isinstance(l.value, dict):
                val = l.value.get(language)
                if val:
                    ret.append(val)
        return ret

    def search_dump(self, data, record):
        ret = {}
        for lang in self.languages:
            ret[lang] = self.get_values(data, lang)
        data[self.attr_name] = ret

    def search_load(self, data, record_cls):
        data.pop(self.attr_name, None)

    def __get__(self, instance, owner):
        return self


class ICUSortField(ICUField):
    """
    A field that adds icu sorting field
    """

    def __init__(self, *, source_field, key=None):
        super().__init__(source_field=source_field, key=key)

    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "object",
                "properties": {
                    lang: {
                        "type": "icu_collation_keyword",
                        "index": False,
                        "language": lang,
                        **setting.get("collation", {}),
                    }
                    for lang, setting in self.languages.items()
                },
            },
        }


class ICUSuggestField(ICUField):
    """
    A field that adds icu-aware suggestion field
    """

    def __init__(self, source_field, key=None):
        super().__init__(source_field=source_field, key=key)

    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "object",
                "properties": {
                    lang: setting.get(
                        "suggest",
                        {
                            "type": "text",
                            "fields": {
                                "original": {
                                    "type": "search_as_you_type",
                                },
                                "no_accent": {
                                    "type": "search_as_you_type",
                                    "analyzer": "accent_removal_analyzer",
                                },
                            },
                        },
                    )
                    for lang, setting in self.languages.items()
                },
            },
        }

    @property
    def mapping_settings(self):
        return {
            "analysis": {
                "analyzer": {
                    "accent_removal_analyzer": {
                        "type": "custom",
                        "tokenizer": "standard",
                        "filter": ["lowercase", "asciifolding"],
                    }
                }
            }
        }


class ICUSearchField(ICUField):
    """
    A field that adds stemming-aware search field
    """

    default_stemming_analyzers = {
        "stemming_analyzer_cs": {
            "tokenizer": "standard",
            "filter": ["stemming_filter_cs"],
        },
        "stemming_analyzer_en": {
            "tokenizer": "standard",
            "filter": ["stemming_filter_en"],
        },
    }

    default_stemming_filters = {
        "stemming_filter_cs": {
            "type": "stemmer",
            "name": "czech",
            "language": "czech",
        },
        "stemming_filter_en": {
            "type": "stemmer",
            "name": "english",
            "language": "english",
        },
    }

    def __init__(self, source_field, key=None):
        super().__init__(source_field=source_field, key=key)

    @property
    def mapping(self):
        return {
            self.attr_name: {
                "type": "object",
                "properties": {
                    lang: setting.get(
                        "search",
                        {
                            "type": "text",
                            "analyzer": f"stemming_analyzer_{lang}",
                        },
                    )
                    for lang, setting in self.languages.items()
                },
            },
        }

    @property
    def mapping_settings(self):
        return {
            "analysis": {
                "analyzer": current_app.config.get(
                    "OAREPO_ICU_SEARCH_ANALYZERS", self.default_stemming_analyzers
                ),
                "filter": current_app.config.get(
                    "OAREPO_ICU_SEARCH_FILTERS", self.default_stemming_filters
                ),
            }
        }
