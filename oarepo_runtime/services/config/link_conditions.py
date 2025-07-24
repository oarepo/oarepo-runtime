from invenio_records.api import RecordBase
from abc import abstractmethod
from logging import getLogger

from invenio_records_resources.records.api import FileRecord, Record
from ..utils import (
    get_record_service_for_record,
)
from ...records.drafts import get_draft
from invenio_pidstore.errors import PIDDoesNotExistError, PIDUnregistered

log = getLogger(__name__)

class Condition:
    @abstractmethod
    def __call__(self, obj, ctx: dict):
        raise NotImplementedError

    def __and__(self, other):
        return type(
            "CompositeCondition",
            (Condition,),
            {"__call__": lambda _, obj, ctx: self(obj, ctx) and other(obj, ctx)},
        )()

    def __or__(self, other):
        return type(
            "CompositeCondition",
            (Condition,),
            {"__call__": lambda _, obj, ctx: self(obj, ctx) or other(obj, ctx)},
        )()

class has_permission(Condition):
    def __init__(self, action_name):
        self.action_name = action_name

    def __call__(self, obj: RecordBase, ctx: dict):
        if isinstance(obj, FileRecord):
            obj = obj.record
        service = get_record_service_for_record(obj)
        try:
            return service.check_permission(
                action_name=self.action_name, record=obj, **ctx
            )
        except Exception as e:
            log.exception(f"Unexpected exception {e}.")

class has_draft_permission(Condition):
    def __init__(self, action_name):
        self.action_name = action_name

    def __call__(self, obj: RecordBase, ctx: dict):
        draft_record = get_draft(obj)
        if not draft_record:
            return False
        service = get_record_service_for_record(obj)
        try:
            return service.check_permission(
                action_name=self.action_name, record=draft_record, **ctx
            )
        except Exception as e:
            log.exception(f"Unexpected exception {e}.")
            return False

class has_draft(Condition):
    """Shortcut for links to determine if record is either a draft or a published one with a draft associated."""

    def __call__(self, obj: Record, ctx: dict):
        if getattr(obj, "is_draft", False):
            return True
        if getattr(obj, "has_draft", False):
            return True
        return False


class has_published_record(Condition):
    def __call__(self, obj: Record, ctx: dict):
        service = get_record_service_for_record(obj)
        try:
            service.record_cls.pid.resolve(obj["id"])
        except (PIDUnregistered, PIDDoesNotExistError):
            return False
        return True

class is_published_record(Condition):
    """Shortcut for links to determine if record is a published record."""

    def __call__(self, obj: Record, ctx: dict):
        return not getattr(obj, "is_draft", False)