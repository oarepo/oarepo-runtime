import warnings
from abc import abstractmethod
from logging import getLogger

from invenio_pidstore.errors import PIDDoesNotExistError, PIDUnregistered
from invenio_records.api import RecordBase
from invenio_records_resources.records.api import FileRecord, Record

from ...datastreams.utils import (
    get_file_service_for_file_record_class,
    get_file_service_for_record_class,
    get_record_service_for_record,
)

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


class is_published_record(Condition):
    """Shortcut for links to determine if record is a published record."""

    def __call__(self, obj: Record, ctx: dict):
        return not getattr(obj, "is_draft", False)


class is_draft_record(Condition):
    """Shortcut for links to determine if record is a draft record."""

    def __call__(self, obj: Record, ctx: dict):
        return getattr(obj, "is_draft", False)


class has_draft(Condition):
    """Shortcut for links to determine if record is either a draft or a published one with a draft associated."""

    def __call__(self, obj: Record, ctx: dict):
        if getattr(obj, "is_draft", False):
            return True
        if getattr(obj, "has_draft", False):
            return True
        return False


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


class has_file_permission(has_permission):
    def __call__(self, obj: RecordBase, ctx: dict):
        if isinstance(obj, FileRecord):
            obj = obj.record
        service = get_file_service_for_record_class(type(obj))
        try:
            return service.check_permission(
                action_name=self.action_name, record=obj, **ctx
            )
        except Exception as e:
            log.exception(f"Unexpected exception {e}.")


class has_permission_file_service(has_file_permission):
    def __init__(self, action_name):
        warnings.warn(
            "has_permission_file_service is deprecated, use has_file_permission instead",
            DeprecationWarning,
        )
        super().__init__(action_name)


class has_published_record(Condition):
    def __call__(self, obj: Record, ctx: dict):
        service = get_record_service_for_record(obj)
        try:
            service.record_cls.pid.resolve(obj["id"])
        except (PIDUnregistered, PIDDoesNotExistError):
            return False
        return True
