# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT
"""Cap the number of messages a single bulk-indexing task consumes.

Background
----------
Invenio indexes records asynchronously. Services publish "index"/"delete"
messages to per-indexer RabbitMQ queues, and Celery beat runs
``invenio_records_resources.tasks.manage_indexer_queues`` every 10 seconds
(``CELERY_BEAT_SCHEDULE["indexer"]`` in invenio-app-rdm). For every indexer
queue that has messages, it sends a ``invenio_indexer.tasks.process_bulk_queue``
task to the ``celery`` queue.

``RecordIndexer.process_bulk_queue`` drains the indexer queue via
``kombu.compat.Consumer.iterqueue(limit=bulk_index_max_items)`` and streams
the documents to OpenSearch ``_bulk`` in chunks of 500.

The problem
-----------
``bulk_index_max_items`` is only a ``RecordIndexer`` constructor argument.
There is no config key for it, and neither the services
(``RecordIndexerMixin.indexer``) nor the Celery task pass it, so it is always
``None`` and ``iterqueue`` runs **until the indexer queue is empty**.
Consequences during a large reindex or a bulk import:

* A single ``process_bulk_queue`` task runs for hours. Building index
  documents (dumpers, relation resolution) is the slow part: we measured
  ~5 minutes per 500-document chunk, i.e. ~0.6 s/record, while the ``_bulk``
  HTTP request itself takes ~50 ms.
* The ``INDEXER_MAX_BULK_CONSUMERS`` guard in ``manage_indexer_queues`` never
  triggers. ``iterqueue`` polls with ``basic_get`` and never registers an AMQP
  consumer, so ``queue_declare()`` always reports 0 consumers. A new
  ``process_bulk_queue`` task is therefore sent every 10 seconds for as long
  as the indexer queue is non-empty.
* These long-running tasks occupy all worker pool slots, while the worker
  keeps ``concurrency * worker_prefetch_multiplier`` further messages
  (the extra ``process_bulk_queue`` and ``manage_indexer_queues`` messages)
  delivered but unacknowledged.
* RabbitMQ (>= 3.8.15) enforces ``consumer_timeout`` (default 30 minutes) on
  unacknowledged deliveries. Once it is exceeded, the broker closes the
  channel with::

      PRECONDITION_FAILED - delivery acknowledgement on channel 1 timed out.
      Timeout value used: 1800000 ms.

  Celery treats this as an "Unrecoverable error" and its consumer dies. The
  pool child finishes the bulk task it already has (``_bulk`` requests keep
  appearing in the log), but no new messages are consumed. Indexing then
  silently stops until the worker is restarted.

The fix
-------
Wrap ``RecordIndexer.process_bulk_queue`` so that, when the caller does not
pass ``bulk_index_max_items``, the value is taken from
``INDEXER_BULK_INDEX_MAX_ITEMS``. Patching the class covers every indexer
(RDM records, communities, users, requests, vocabularies, oarepo-model
generated services) without changing each service's ``indexer_cls``.

Each task now ends after a bounded number of records, and
``manage_indexer_queues`` starts the next one within 10 seconds, so overall
throughput is unchanged. Choose the value so that one task finishes well
within ``consumer_timeout``:
``max_items * seconds_per_record << 1800 s``. With ~0.6 s/record, 1000-2000
items is a safe range.

The patch must be active in the **Celery worker** process, because that is
where ``process_bulk_queue`` runs. The worker app is built by
``invenio_app.factory.create_ui``, so register this through
``invenio_base.apps``.

What this does not fix
----------------------
``manage_indexer_queues`` still sends a redundant ``process_bulk_queue`` every
10 seconds while the indexer queue is non-empty. With short tasks those
messages no longer wait long enough to hit ``consumer_timeout``. Redundant
tasks that start after the queue is drained exit immediately. For extra
safety, also raise ``consumer_timeout`` on the broker or on the ``celery``
queue (via policy), and/or route ``process_bulk_queue`` to a dedicated queue
and worker.

Note:
----
This fix should be ported to invenio itself.

"""

from __future__ import annotations

from typing import Any

from flask import current_app
from invenio_indexer.api import RecordIndexer

_orig_process_bulk_queue = RecordIndexer.process_bulk_queue


def _process_bulk_queue(
    self: RecordIndexer,
    search_bulk_kwargs: dict[str, Any] | None = None,
    bulk_index_max_items: int | None = None,
) -> int:
    return _orig_process_bulk_queue(
        self,
        search_bulk_kwargs=search_bulk_kwargs,
        bulk_index_max_items=bulk_index_max_items or current_app.config.get("INDEXER_BULK_INDEX_MAX_ITEMS", 1000),
    )


RecordIndexer.process_bulk_queue = _process_bulk_queue
