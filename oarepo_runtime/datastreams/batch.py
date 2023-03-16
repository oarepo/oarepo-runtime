import dataclasses
from typing import Dict, List

from oarepo_runtime.datastreams.datastreams import StreamEntry


@dataclasses.dataclass
class StreamBatch:
    seq: int
    last: bool
    entries: List[StreamEntry]
    context: Dict = dataclasses.field(default_factory=dict)
