from invenio_records_resources.services.custom_fields import BaseCF

from oarepo_runtime.relations.lookup import lookup_key


class ICUSortCF(BaseCF):
    def __init__(
        self, name, language, source_field, country=None, variant=None, field_args=None
    ):
        super().__init__(name=name, field_args=field_args)
        self.language = language
        self.country = country
        self.variant = variant
        self.source_field = source_field

    @property
    def mapping(self):
        ret = {
            "type": "icu_collation_keyword",
            "index": False,
            "language": self.language,
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
    def __init__(self, name, language, source_field, field_args=None):
        super().__init__(name=name, field_args=field_args)
        self.language = language
        self.source_field = source_field

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
