import typing

from invenio_rdm_records.services.schemas.record import RDMRecordSchema
from invenio_records_resources.services.records.schema import (
    BaseRecordSchema as InvenioBaseRecordSchema,
)

import marshmallow as ma


class BaseRecordSchema(InvenioBaseRecordSchema):
    """Base record schema - in addition to invenio exposes $schema as well."""

    _schema = ma.fields.Str(attribute="$schema", data_key="$schema")


class RDMBaseRecordSchema(RDMRecordSchema):
    """Base record schema - in addition to invenio exposes $schema as well."""

    _schema = ma.fields.Str(attribute="$schema", data_key="$schema")


class DictOnlySchema(ma.Schema):
    def get_attribute(self, obj: typing.Any, attr: str, default: typing.Any):
        if not isinstance(attr, int) and "." in attr:
            return _get_value_for_keys_dict_only(obj, attr.split("."), default)
        else:
            return _get_value_for_key_dict_only(obj, attr, default)


def _get_value_for_keys_dict_only(obj, keys, default):
    if len(keys) == 1:
        return _get_value_for_key_dict_only(obj, keys[0], default)
    else:
        return _get_value_for_keys_dict_only(
            _get_value_for_key_dict_only(obj, keys[0], default), keys[1:], default
        )


def _get_value_for_key_dict_only(obj, key, default):
    try:
        return obj[key]
    except (KeyError, IndexError, TypeError, AttributeError):
        return default
