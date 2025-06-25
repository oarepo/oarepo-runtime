from flask_resources import BaseListSchema
from invenio_records_resources.proxies import current_service_registry
from marshmallow import fields, post_dump


class FilteredUIListSchema(BaseListSchema):
    params = fields.Raw()

    @post_dump
    def after_dump(self, data, *args, **kwargs):
        service = self.context["service"]
        params = data.setdefault("params", {})
        service_config = current_service_registry.get(service).config
        search_options = service_config.search
        facets = search_options.facets
        translated_params = {}

        for k, v in params.items():
            facet = facets.get(k)
            if not facet:
                continue
            translated_params.setdefault(k, {})
            translated_params[k]["label"] = facet._label
            value_labels_attr = getattr(facet, "_value_labels", None)
            if not value_labels_attr:
                translated_params[k]["value_labels"] = [{"key": key} for key in v]
                continue

            value_labels = {}
            if callable(value_labels_attr):
                value_labels = facet._value_labels(v)
            elif isinstance(value_labels_attr, dict):
                value_labels = facet._value_labels

            if value_labels:
                translated_params[k]["value_labels"] = [
                    {"key": key, "label": value_labels.get(key, key)} for key in v
                ]

        data["filters_l10n"] = translated_params
        return data
