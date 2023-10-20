from invenio_records_resources.services.custom_fields import BaseCF

from oarepo_runtime.relations.lookup import lookup_key


class ICUSortCF(BaseCF):
    def __init__(
        self,
        language,
        opensearch_language,
        source_field,
        cf_name=None,
        country=None,
        variant=None,
        sort_option=None,
        field_args=None,
    ):
        super().__init__(name=cf_name or language, field_args=field_args)
        self.opensearch_language = opensearch_language
        self.country = country
        self.variant = variant
        self.source_field = source_field
        self.sort_option = sort_option or source_field.rsplit(".", maxsplit=1)[-1]
        self.language = language

    @property
    def mapping(self):
        ret = {
            "type": "icu_collation_keyword",
            "index": False,
            "language": self.opensearch_language,
        }
        if self.country:
            ret["country"] = self.country

        if self.variant:
            ret["variant"] = self.variant

        return ret

    @property
    def field(self):
        return None

    def dump(self, record, cf_key="custom_fields"):
        ret = []
        for l in lookup_key(record, self.source_field):
            ret.append(l.value)
        record.setdefault(cf_key, {})[self.name] = ret

    def load(self, record, cf_key="custom_fields"):
        record.pop(cf_key, None)


class ICUSuggestCF(BaseCF):
    def __init__(
        self, language, opensearch_language, source_field, cf_name=None, field_args=None
    ):
        super().__init__(name=cf_name or language, field_args=field_args)
        self.opensearch_language = opensearch_language
        self.source_field = source_field
        self.language = language

    @property
    def mapping(self):
        ret = {
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
        }
        return ret

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

    @property
    def field(self):
        return None

    def dump(self, record, cf_key="custom_fields"):
        ret = []
        for l in lookup_key(record, self.source_field):
            ret.append(l.value)
        record.setdefault(cf_key, {})[self.name] = ret

    def load(self, record, cf_key="custom_fields"):
        record.pop(cf_key, None)
