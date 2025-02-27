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

from deepmerge import always_merger
from oarepo_runtime.records.systemfields.mapping import MappingSystemFieldMixin
import json
import os

from pathlib import Path

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
        record_class = getattr(config, "record_cls", None)
        if record_class:
            prepare_cf_index(record_class, config)
            parent_class = getattr(record_class, "parent_record_cls", None)
            prepare_parent_mapping(parent_class, config)
            prepare_cf_index(parent_class, config, path=["parent", "properties"])


def prepare_cf_index(record_class, config, path=[]):
    if not record_class:
        return

    for fld in get_mapping_fields(record_class):
        # get mapping
        mapping = fld.mapping
        settings = fld.mapping_settings
        dynamic_templates = fld.dynamic_templates

        for pth in reversed(path):
            mapping = {pth: mapping}

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


def prepare_parent_mapping(parent_class, config):
    if not parent_class:
        return

    if not config.record_cls.index._name:
        return

    script_dir = str(Path(__file__).resolve().parent)
    path_parts = script_dir.split('/')
    path_parts = path_parts[:-2]
    base_path = '/'.join(path_parts)
    mapping_path = f"{base_path}/records/mappings/rdm_parent_mapping.json"

    with open(mapping_path, 'r') as f:
        rdm_parent = json.load(f)

    parent_mapping = {
        "parent": {
            "type": "object",
            "properties": {
                "created": {
                    "type": "date",
                    "format": "strict_date_time||strict_date_time_no_millis||basic_date_time||basic_date_time_no_millis||basic_date||strict_date||strict_date_hour_minute_second||strict_date_hour_minute_second_fraction",
                },
                "id": {"type": "keyword", "ignore_above": 1024},
                "pid": {
                    "properties": {
                        "obj_type": {"type": "keyword", "ignore_above": 1024},
                        "pid_type": {"type": "keyword", "ignore_above": 1024},
                        "pk": {"type": "long"},
                        "status": {"type": "keyword", "ignore_above": 1024},
                    }
                },
                "updated": {
                    "type": "date",
                    "format": "strict_date_time||strict_date_time_no_millis||basic_date_time||basic_date_time_no_millis||basic_date||strict_date||strict_date_hour_minute_second||strict_date_hour_minute_second_fraction",
                },
                "uuid": {"type": "keyword", "ignore_above": 1024},
                "version_id": {"type": "long"},
            },
        }
    }
    parent_mapping_merged = always_merger.merge(parent_mapping, {
        "parent": {
            "properties": rdm_parent
        }
    })
    # upload mapping
    try:
        record_index = dsl.Index(
            build_alias_name(
                config.record_cls.index._name,
            ),
            using=current_search_client,
        )
        update_index(record_index, {}, parent_mapping_merged)

        if hasattr(config, "draft_cls"):
            draft_index = dsl.Index(
                build_alias_name(
                    config.draft_cls.index._name,
                ),
                using=current_search_client,
            )
            update_index(record_index, {}, parent_mapping_merged)

    except search.RequestError as e:
        click.secho("An error occurred while creating parent mapping.", fg="red")
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
