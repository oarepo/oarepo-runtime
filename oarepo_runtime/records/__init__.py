from typing import Type

from invenio_records_resources.records import Record

from ..datastreams.utils import get_record_service_for_record


def select_record_for_update(record_cls: Type[Record], persistent_identifier):
    """Select a record for update."""
    resolved_record = record_cls.pid.resolve(persistent_identifier)
    model_id = resolved_record.model.id
    obj = record_cls.model_cls.query.filter_by(id=model_id).with_for_update().one()
    return record_cls(obj.data, model=obj)


def is_published_record(record, ctx):
    """Shortcut for links to determine if record is a published record."""
    return not getattr(record, "is_draft", False)


def is_draft_record(record, ctx):
    """Shortcut for links to determine if record is a draft record."""
    return getattr(record, "is_draft", False)


def has_draft(record, ctx):
    """Shortcut for links to determine if record is either a draft or a published one with a draft associated."""
    if getattr(record, "is_draft", False):
        return True
    if getattr(record, "has_draft", False):
        return True
    return False

class Condition:
    def __init__(self, *conditions):
        self.conditions = conditions

    def __call__(self, obj, ctx):
        results = [cond(obj, ctx) for cond in self.conditions]
        return all(results)

def has_permission(action_name):
    def _has_permission(record, ctx):
        service = get_record_service_for_record(record)
        return service.check_permission(action_name=action_name, record=record, **ctx) #will this always work without other arguments; ie will the requiered arguments always be in ctx?
    return _has_permission