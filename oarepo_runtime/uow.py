import logging
import traceback

from flask import current_app
from invenio_indexer.api import bulk
from invenio_records_resources.services.uow import (
    RecordCommitOp,
    RecordDeleteOp,
    UnitOfWork,
)
from opensearchpy.helpers import BulkIndexError, bulk
from opensearchpy.helpers import expand_action as default_expand_action

log = logging.getLogger("bulk_uow")


class CachingUnitOfWork(UnitOfWork):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.cache = {}


class BulkRecordCommitOp(RecordCommitOp):
    def __init__(self, rc: RecordCommitOp):
        super().__init__(rc._record, rc._indexer, rc._index_refresh)
        self._previous = rc

    def on_register(self, uow):
        self._previous.on_register(uow)

    def on_commit(self, uow):
        """Postponed."""

    def get_index_action(self):
        if self._indexer is None:
            return None

        index = self._indexer.record_to_index(self._record)
        arguments = {}
        body = self._indexer._prepare_record(self._record, index, arguments)
        index = self._indexer._prepare_index(index)

        action = {
            "_op_type": "index",
            "_index": index,
            "_id": str(self._record.id),
            "_version": self._record.revision_id,
            "_version_type": self._indexer._version_type,
            "_source": body,
        }
        action.update(arguments)
        return action


class BulkRecordDeleteOp(RecordDeleteOp):
    def __init__(self, rc: RecordDeleteOp):
        super().__init__(rc._record, rc._indexer, rc._index_refresh)
        self._previous = rc

    def on_register(self, uow):
        self._previous.on_register(uow)

    def on_commit(self, uow):
        """Postponed."""

    def get_index_action(self):
        if self._indexer is None:
            return None
        index = self._indexer.record_to_index(self._record)
        index = self._indexer._prepare_index(index)

        action = {
            "_op_type": "delete",
            "_index": index,
            "_id": str(self._record.id),
        }
        return action


class BulkUnitOfWork(CachingUnitOfWork):
    _last_stack_trace = None
    _last_exception = None

    def register(self, op):
        if isinstance(op, RecordCommitOp):
            op = BulkRecordCommitOp(op)
        elif isinstance(op, RecordDeleteOp):
            op = BulkRecordDeleteOp(op)
        return super().register(op)

    def commit(self):
        super().commit()

        # do bulk indexing
        bulk_data = []
        indexer = None
        for op in self._operations:
            if isinstance(op, BulkRecordCommitOp) or isinstance(op, BulkRecordDeleteOp):
                indexer = indexer or op._indexer
                index_action = op.get_index_action()
                if index_action:
                    bulk_data.append(index_action)
        if indexer:
            req_timeout = current_app.config["INDEXER_BULK_REQUEST_TIMEOUT"]
            try:
                resp = bulk(
                    indexer.client,
                    bulk_data,
                    stats_only=True,
                    request_timeout=req_timeout,
                    expand_action_callback=default_expand_action,
                    refresh=True,
                )
            except BulkIndexError as e:
                raise e

    def _mark_dirty(self):
        """Mark the unit of work as dirty."""
        if self._dirty:
            if self._last_stack_trace:
                log.error(
                    f"UnitOfWork already committed or rolled back at {self._last_stack_trace}. "
                    f"Previous exception was {self._last_exception}"
                )

            raise RuntimeError(
                f"The unit of work is already committed or rolledback. "
                f"Set error level for logger 'bulk_uow' to at least WARNING "
                f"to see the stack trace of the previous invocation."
            )

        self._dirty = True
        if log.getEffectiveLevel() >= logging.WARNING:
            try:
                self._last_stack_trace = "\n"
                self._last_stack_trace += "\n".join(traceback.format_stack())
            except:
                pass

            try:
                self._last_exception = traceback.format_exc()
            except:
                pass


__all__ = ["BulkUnitOfWork"]
