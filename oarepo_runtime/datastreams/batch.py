import dataclasses
from typing import Dict, List

from oarepo_runtime.datastreams.datastreams import StreamEntry


@dataclasses.dataclass
class StreamBatch:
    seq: int
    last: bool
    entries: List[StreamEntry]
    context: Dict = dataclasses.field(default_factory=dict)

    def copy(self, **kwargs):
        return type(self)(
            seq=kwargs.get("seq", self.seq),
            last=kwargs.get("last", self.last),
            entries=kwargs.get("entries", self.entries),
            context=kwargs.get("context", self.context),
        )
