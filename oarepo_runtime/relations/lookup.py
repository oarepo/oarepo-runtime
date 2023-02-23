import dataclasses
from typing import Any, Tuple


@dataclasses.dataclass
class LookupResult:
    path: Tuple[str]
    value: Any


def lookup_key(record, key):
    """more generic version of dict_lookup, for arrays does not look up by index but returns all members of array"""

    def _internal_lookup_key(key, data, path: Tuple):
        if isinstance(data, (tuple, list)):
            for idx, d in enumerate(data):
                yield from _internal_lookup_key(key, d, path + (idx,))
            return
        if not key:
            yield LookupResult(path, data)
            return
        if not isinstance(data, dict):
            return
        if key[0] in data:
            yield from _internal_lookup_key(key[1:], data[key[0]], path + (key[0],))

    key = key.split(".")
    return list(_internal_lookup_key(key, record, tuple()))
