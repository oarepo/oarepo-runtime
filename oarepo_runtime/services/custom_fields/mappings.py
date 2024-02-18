import inspect
from typing import Iterable

import click
import deepmerge
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.custom_fields.mappings import (
    Mapping as InvenioMapping,
)
from invenio_records_resources.services.records.config import RecordServiceConfig
from invenio_records_resources.services.records.service import RecordService
from invenio_search import current_search_client
from invenio_search.engine import dsl, search
from invenio_search.utils import build_alias_name

from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin


class Mapping(InvenioMapping):
    @classmethod
    def properties_for_fields(
        cls, given_fields_names, available_fields, field_name="custom_fields"
    ):
        """Prepare search mapping properties for each field."""

        properties = {}
        for field in cls._get_fields(given_fields_names, available_fields):
            if field_name:
                properties[f"{field_name}.{field.name}"] = field.mapping
            else:
                properties[field.name] = field.mapping

        return properties

    @classmethod
    def settings_for_fields(
        cls, given_fields_names, available_fields, field_name="custom_fields"
    ):
        """Prepare mapping settings for each field."""

        settings = {}
        for field in cls._get_fields(given_fields_names, available_fields):
            if not hasattr(field, "mapping_settings"):
                continue
            settings = deepmerge.always_merger.merge(settings, field.mapping_settings)

        return settings

    @classmethod
    def _get_fields(cls, given_fields_names, available_fields):
        fields = []
        if given_fields_names:  # create only specified fields
            given_fields_names = set(given_fields_names)
            for a_field in available_fields:
                if a_field.name in given_fields_names:
                    fields.append(a_field)
                    given_fields_names.remove(a_field.name)
                if len(given_fields_names) == 0:
                    break
        else:  # create all fields
            fields = available_fields
        return fields


# pieces taken from https://github.com/inveniosoftware/invenio-rdm-records/blob/master/invenio_rdm_records/cli.py
# as cf initialization is not supported directly in plain invenio
def prepare_cf_indices():
    service: RecordService
    for service in current_service_registry._services.values():
        config: RecordServiceConfig = service.config
        prepare_cf_index(config)


def prepare_cf_index(config: RecordServiceConfig):
    record_class = getattr(config, "record_cls", None)
    if not record_class:
        return

    for fld in get_mapping_fields(record_class):
        # get mapping
        mapping = fld.mapping
        settings = fld.mapping_settings
        dynamic_templates = fld.dynamic_templates

        # upload mapping
        try:
            record_index = dsl.Index(
                build_alias_name(
                    config.record_cls.index._name,
                ),
                using=current_search_client,
            )
            update_index(record_index, settings, mapping)

            if hasattr(config, "draft_cls"):
                draft_index = dsl.Index(
                    build_alias_name(
                        config.draft_cls.index._name,
                    ),
                    using=current_search_client,
                )
                update_index(draft_index, settings, mapping, dynamic_templates)

        except search.RequestError as e:
            click.secho("An error occurred while creating custom fields.", fg="red")
            click.secho(e.info["error"]["reason"], fg="red")


def update_index(record_index, settings, mapping, dynamic_templates=None):
    if settings:
        record_index.close()
        record_index.put_settings(body=settings)
        record_index.open()
    body = {}
    if mapping:
        body["properties"] = mapping
    if dynamic_templates:
        body["dynamic_templates"] = dynamic_templates
    if body:
        record_index.put_mapping(body=body)


def get_mapping_fields(record_class) -> Iterable[MappingSystemFieldMixin]:
    for cfg_name, cfg_value in inspect.getmembers(
        record_class, lambda x: isinstance(x, MappingSystemFieldMixin)
    ):
        yield cfg_value
