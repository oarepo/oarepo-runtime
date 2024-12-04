from typing import Type

from deprecated import deprecated
from invenio_records_resources.records import Record


def select_record_for_update(record_cls: Type[Record], persistent_identifier):
    """Select a record for update."""
    resolved_record = record_cls.pid.resolve(persistent_identifier)
    model_id = resolved_record.model.id
    obj = record_cls.model_cls.query.filter_by(id=model_id).with_for_update().one()
    return record_cls(obj.data, model=obj)


@deprecated("Moved to oarepo_runtime.services.config.link_conditions")
def is_published_record_function():
    """Shortcut for links to determine if record is a published.

    This function is deprecated. Use oarepo_runtime.services.config.is_published_record instead.
    """
    from oarepo_runtime.services.config.link_conditions import is_published_record

    return is_published_record()


@deprecated("Moved to oarepo_runtime.services.config.link_conditions")
def is_draft_record_function():
    """Shortcut for links to determine if record is a draft record.

    This function is deprecated. Use oarepo_runtime.services.config.is_draft_record instead.
    """
    from oarepo_runtime.services.config.link_conditions import is_draft_record

    return is_draft_record()


@deprecated("Moved to oarepo_runtime.services.config.link_conditions")
def has_draft_function():
    """Shortcut for links to determine if record is either a draft or a published one with a draft associated.

    This function is deprecated. Use oarepo_runtime.services.config.has_draft instead.
    """
    from oarepo_runtime.services.config.link_conditions import has_draft

    return has_draft()


is_published_record = is_published_record_function()
is_draft = is_draft_record_function()
has_draft = has_draft_function()
