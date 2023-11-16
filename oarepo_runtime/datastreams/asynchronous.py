import logging
from typing import Any, Dict, List, Union

import celery
from celery.canvas import Signature as CelerySignature
from celery.canvas import chain
from celery.result import allow_join_result
from flask_principal import (
    ActionNeed,
    Identity,
    ItemNeed,
    Need,
    RoleNeed,
    TypeNeed,
    UserNeed,
)

from oarepo_runtime.datastreams.datastreams import (
    AbstractDataStream,
    DataStreamChain,
    Signature,
)

from .datastreams import DataStreamCallback, StreamBatch
from .json import JSONObject
from .types import StreamEntryError
from .writers import BaseWriter

timing = logging.getLogger("oai.harvester.timing")
log = logging.getLogger("datastreams")


class AsynchronousDataStream(AbstractDataStream):
    def __init__(
        self,
        *,
        readers: List[Union[Signature, Any]],
        writers: List[Union[Signature, Any]],
        transformers: List[Union[Signature, Any]] = None,
        callback: Union[DataStreamCallback, Any],
        batch_size=100,
        on_background=True,
        reader_callback=None,
    ):
        super().__init__(
            readers=readers,
            writers=writers,
            transformers=transformers,
            callback=callback,
            batch_size=batch_size,
            reader_callback=reader_callback,
        )
        self._on_background = on_background

    def build_chain(self, identity) -> DataStreamChain:
        return AsynchronousDataStreamChain(
            transformers=self._transformers,
            writers=self._writers,
            on_background=self._on_background,
            identity=identity,
        )

    def _reader_error(self, reader, exception):
        self._callback.apply(
            kwargs={
                "callback": f"reader_error",
                "exception": StreamEntryError.from_exception(exception).json,
            }
        )


class AsynchronousDataStreamChain(DataStreamChain):
    def __init__(
        self,
        identity: Identity,
        transformers: List[Signature],
        writers: List[Signature],
        on_background=True,
    ):
        self._transformers = transformers
        self._writers = writers
        self._on_background = on_background
        self._identity = identity

    def process(self, batch: StreamBatch, callback: CelerySignature):
        chain = self._prepare_chain(callback)
        self._call(chain, batch=batch.json)

    def _prepare_chain(self, callback: CelerySignature):
        chain_def = [
            datastreams_call_callback.signature(
                (), kwargs={"callback": callback, "callback_name": "batch_started"}
            )
        ]
        serialized_identity = serialize_identity(self._identity)
        if self._transformers:
            for transformer in self._transformers:
                chain_def.append(
                    run_datastream_processor.signature(
                        kwargs={
                            "processor": transformer.json,
                            "identity": serialized_identity,
                            "callback": callback,
                        }
                    )
                )

        for writer in self._writers:
            chain_def.append(
                run_datastream_processor.signature(
                    kwargs={
                        "processor": writer.json,
                        "identity": serialized_identity,
                        "callback": callback,
                    }
                )
            )

        chain_def.append(
            datastreams_call_callback.signature(
                (),
                kwargs=dict(
                    callback=callback,
                    callback_name="batch_finished",
                    identity=serialized_identity,
                ),
            )
        )

        chain_sig = chain(*chain_def)
        chain_sig.link_error(
            datastreams_error_callback.signature(
                (),
                kwargs=dict(
                    callback=callback,
                    callback_name="error",
                    identity=serialized_identity,
                ),
            )
        )
        return chain_sig

    def _call(self, sig, **kwargs):
        if self._on_background:
            call = sig.apply_async
        else:
            call = sig.apply
        call([], kwargs)

    def finish(self, callback: Signature):
        "nothing to finish here, dumpers needing finish (such as file dumpers) are not supported in async"


@celery.shared_task
def run_datastream_processor(batch: Dict, *, processor: JSONObject, identity, callback):
    identity = deserialize_identity(identity)
    processor_signature = Signature.from_json(processor)
    deserialized_batch: StreamBatch = StreamBatch.from_json(batch)

    processor = processor_signature.resolve(identity=identity)
    try:
        if isinstance(processor, BaseWriter):
            deserialized_batch = (
                processor.write(deserialized_batch) or deserialized_batch
            )
        else:
            deserialized_batch = (
                processor.apply(deserialized_batch) or deserialized_batch
            )

    except Exception as ex:
        log.exception("Error processing batch inside %s", processor_signature)

        err = StreamEntryError.from_exception(ex)
        deserialized_batch.errors.append(err)
        callback.apply(
            (),
            {
                "batch": deserialized_batch.json,
                "identity": serialize_identity(identity),
                "callback": f"{processor_signature.kind}_error",
                "exception": err.json,
            },
        )
    return deserialized_batch.json


@celery.shared_task
def datastreams_call_callback(
    batch: Dict, *, identity=None, callback, callback_name, **kwargs
):
    callback = CelerySignature(callback)
    callback.apply(
        kwargs=dict(batch=batch, identity=identity, callback=callback_name, **kwargs)
    )
    return batch


@celery.shared_task
def datastreams_error_callback(
    parent_task_id, *, identity=None, callback, callback_name, **kwargs
):
    with allow_join_result():
        from celery import current_app

        result = current_app.AsyncResult(parent_task_id)
        result.get(propagate=False)

        callback = CelerySignature(callback)
        callback.apply(
            kwargs=dict(
                batch={},
                identity=identity,
                callback=callback_name,
                result=result.result,
                traceback=result.traceback,
                **kwargs,
            )
        )


def serialize_identity(identity):
    return {
        "id": identity.id,
        "auth_type": identity.auth_type,
        "provides": [
            {"type": type(x).__name__, "params": x._asdict()} for x in identity.provides
        ],
    }


def deserialize_identity(identity_dict):
    if identity_dict is None:
        return None
    ret = Identity(id=identity_dict["id"], auth_type=identity_dict["auth_type"])
    for provide in identity_dict["provides"]:
        clz = {
            "Need": Need,
            "UserNeed": UserNeed,
            "RoleNeed": RoleNeed,
            "TypeNeed": TypeNeed,
            "ActionNeed": ActionNeed,
            "ItemNeed": ItemNeed,
        }[provide["type"]]

        ret.provides.add(clz(**provide["params"]))
    return ret
