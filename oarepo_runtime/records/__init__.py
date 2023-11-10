from typing import Type

from invenio_records_resources.records import Record


def select_record_for_update(record_cls: Type[Record], persistent_identifier):
    """Select a record for update."""
    resolved_record = record_cls.pid.resolve(persistent_identifier)
    model_id = resolved_record.model.id
    obj = record_cls.model_cls.query.filter_by(id=model_id).with_for_update().one()
    return record_cls(obj.data, model=obj)
