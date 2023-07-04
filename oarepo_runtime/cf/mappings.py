import inspect
from typing import Iterable, List

import click
from flask import current_app
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.custom_fields import BaseCF
from invenio_records_resources.services.custom_fields.mappings import (
    Mapping as InvenioMapping,
)
from invenio_records_resources.services.custom_fields.validate import (
    validate_custom_fields,
)
from invenio_records_resources.services.records.config import RecordServiceConfig
from invenio_records_resources.services.records.service import RecordService
from invenio_search import current_search_client
from invenio_search.engine import dsl, search
from invenio_search.utils import build_alias_name

from oarepo_runtime.cf import CustomFieldsMixin


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
def prepare_cf_indices(field_names: List[str] = None):
    service: RecordService
    for service in current_service_registry._services.values():
        config: RecordServiceConfig = service.config
        prepare_cf_index(config, field_names)


def prepare_cf_index(config: RecordServiceConfig, field_names: List[str] = None):
    record_class = getattr(config, "record_cls", None)
    if not record_class:
        return

    # try to get custom fields from the record class
    # validate them
    for field_name, available_fields in get_custom_fields(record_class):
        validate_custom_fields(
            given_fields=field_names, available_fields=available_fields, namespaces=[]
        )

        # get mapping
        properties = Mapping.properties_for_fields(
            field_names, available_fields, field_name=field_name
        )
        if not properties:
            continue

        # upload mapping
        try:
            record_index = dsl.Index(
                build_alias_name(
                    config.record_cls.index._name,
                ),
                using=current_search_client,
            )
            record_index.put_mapping(body={"properties": properties})

            if hasattr(config, "draft_cls"):
                draft_index = dsl.Index(
                    build_alias_name(
                        config.draft_cls.index._name,
                    ),
                    using=current_search_client,
                )
                draft_index.put_mapping(body={"properties": properties})

        except search.RequestError as e:
            click.secho("An error occurred while creating custom fields.", fg="red")
            click.secho(e.info["error"]["reason"], fg="red")


def get_custom_fields(record_class) -> Iterable[List[BaseCF]]:
    for cfg_name, cfg_value in inspect.getmembers(
        record_class, lambda x: isinstance(x, CustomFieldsMixin)
    ):
        yield cfg_value._key, current_app.config[cfg_value.config_key]
