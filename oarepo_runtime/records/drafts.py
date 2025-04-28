from invenio_records_resources.records.api import Record

from oarepo_runtime.datastreams.utils import get_record_service_for_record


def has_draft(record: Record) -> bool:
    return get_draft(record) is not None


def get_draft(record: Record) -> Record | None:
    """Get the draft of a published record, if it exists.

    A record can have a draft if:

    - it has a parent record (so, for vocabulary records, this will always be False)
    - if it has a has_draft attribute (that means, it is a published record)
    - the has_draft is True meaning that the record has a draft ('edit metadata' button)
    - if the record has a parent and the parent has a draft (edited 'new version' of the record)
    """
    if getattr(record, "is_draft", False):
        return record
    if not hasattr(record, "parent"):
        return None
    if not hasattr(record, "has_draft"):
        return None

    record_service = get_record_service_for_record(record)
    if not record_service:
        return None

    try:
        # if there is no record service, we cannot check for draft
        if not record_service:
            return None
        return next(
            record_service.config.draft_cls.get_records_by_parent(
                record.parent, with_deleted=False
            )
        )
    except StopIteration:
        # no draft found
        return None
