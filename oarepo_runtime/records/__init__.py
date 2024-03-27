from typing import Type

from invenio_records_resources.records import Record


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
    if getattr(record, 'has_draft', False):
        return True
    return False
