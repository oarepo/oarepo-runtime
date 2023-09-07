from flask import current_app
from invenio_db import db
from invenio_indexer.api import bulk
from invenio_records_resources.services.uow import (
    RecordCommitOp,
    RecordDeleteOp,
    UnitOfWork,
)
from opensearchpy.helpers import BulkIndexError, bulk
from opensearchpy.helpers import expand_action as default_expand_action


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
        index = self._indexer.record_to_index(self._record)
        index = self._indexer._prepare_index(index)

        action = {
            "_op_type": "delete",
            "_index": index,
            "_id": str(self._record.id),
        }
        return action


class BulkUnitOfWork(CachingUnitOfWork):
    def register(self, op):
        if isinstance(op, RecordCommitOp):
            op = BulkRecordCommitOp(op)
        elif isinstance(op, RecordDeleteOp):
            op = BulkRecordDeleteOp(op)
        return super().register(op)

    def commit(self):
        # prevent session to extend outside of this call
        with db.session.begin_nested():
            super().commit()

        # do bulk indexing
        bulk_data = []
        indexer = None
        for op in self._operations:
            if isinstance(op, BulkRecordCommitOp) or isinstance(op, BulkRecordDeleteOp):
                indexer = op._indexer
                bulk_data.append(op.get_index_action())
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


__all__ = ["BulkUnitOfWork"]