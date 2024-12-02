from abc import abstractmethod

from invenio_pidstore.errors import PIDDoesNotExistError, PIDUnregistered
from invenio_records_resources.records.api import FileRecord
import traceback
from ...datastreams.utils import (
    get_file_service_for_file_record_class,
    get_file_service_for_record_class,
    get_record_service_for_record,
)


class Condition:

    @abstractmethod
    def __call__(self, obj, ctx):
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


class is_published_record(Condition):
    """Shortcut for links to determine if record is a published record."""

    def __call__(self, record, ctx):
        return not getattr(record, "is_draft", False)


class is_draft_record(Condition):
    """Shortcut for links to determine if record is a draft record."""

    def __call__(self, record, ctx):
        return getattr(record, "is_draft", False)


class has_draft(Condition):
    """Shortcut for links to determine if record is either a draft or a published one with a draft associated."""

    def __call__(self, record, ctx):
        if getattr(record, "is_draft", False):
            return True
        if getattr(record, "has_draft", False):
            return True
        return False


class has_permission(Condition):
    def __init__(self, action_name):
        self.action_name = action_name

    def __call__(self, record, ctx):
        if isinstance(record, FileRecord):
            record = record.record
        service = get_record_service_for_record(record)
        try:
            return service.check_permission(
                action_name=self.action_name, record=record, **ctx
            )
        except Exception:
            traceback.print_exc()



class has_permission_file_service(has_permission):

    def __call__(self, record, ctx):
        if isinstance(record, FileRecord):
            service = get_file_service_for_file_record_class(type(record))
        else:
            service = get_file_service_for_record_class(type(record))
        try:
            return service.check_permission(
                action_name=self.action_name, record=record, **ctx
            )
        except Exception:
            traceback.print_exc()


class has_published_record(Condition):

    def __call__(self, record, ctx):
        service = get_record_service_for_record(record)
        try:
            service.record_cls.pid.resolve(record["id"])
        except (PIDUnregistered, PIDDoesNotExistError):
            return False
        return True
