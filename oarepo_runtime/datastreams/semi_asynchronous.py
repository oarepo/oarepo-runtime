#
# This package was taken from Invenio vocabularies and modified to be more universal
#
import logging
from typing import List

from celery import shared_task
from celery.canvas import Signature as CelerySignature

from .asynchronous import (
    AsynchronousDataStream,
    AsynchronousDataStreamChain,
    deserialize_identity,
    serialize_identity,
)
from .datastreams import DataStreamChain, Signature
from .transformers import BaseTransformer
from .types import JSONObject, StreamBatch, StreamEntryError

log = logging.getLogger("datastreams")


class SemiAsynchronousDataStreamChain(AsynchronousDataStreamChain):
    def _prepare_chain(self, callback: CelerySignature):
        serialized_identity = serialize_identity(self._identity)
        return run_semi_asynchronous_datastream_processor.s(
            transformers=[tr.json for tr in self._transformers],
            writers=[wr.json for wr in self._writers],
            identity=serialized_identity,
            callback=callback,
        )


class SemiAsynchronousDataStream(AsynchronousDataStream):
    """Data stream."""

    def build_chain(self, identity) -> DataStreamChain:
        return SemiAsynchronousDataStreamChain(
            transformers=self._transformers,
            writers=self._writers,
            on_background=self._on_background,
            identity=identity,
        )


@shared_task
def run_semi_asynchronous_datastream_processor(
    batch: JSONObject,
    *,
    transformers: List[JSONObject],
    writers: List[JSONObject],
    identity: JSONObject,
    callback: CelerySignature,
):
    """Run datastream processor."""

    callback.apply(kwargs={"callback": "batch_started", "batch": batch})

    batch = StreamBatch.from_json(batch)
    identity = deserialize_identity(identity)

    for signature in (transformers or []) + (writers or []):
        signature = Signature.from_json(signature)
        try:
            processor = signature.resolve(identity=identity)
            if isinstance(processor, BaseTransformer):
                batch = processor.apply(batch) or batch
            else:
                batch = processor.write(batch) or batch
        except Exception as ex:
            if log.getEffectiveLevel():
                log.error(
                    "Unexpected error in %s: %s",
                    repr(signature),
                    repr(batch),
                )
            err = StreamEntryError.from_exception(ex)
            batch.errors.append(err)
            callback.apply(
                (),
                {
                    "batch": batch.json,
                    "identity": serialize_identity(identity),
                    "callback": f"{signature.kind.value}_error",
                    "exception": err.json,
                },
            )

    callback.apply(kwargs={"callback": "batch_finished", "batch": batch.json})

    return None  # do not return anything to avoid redis pollution
