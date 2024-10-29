import dataclasses
from typing import Any, Callable, List, Protocol, Tuple

from oarepo_runtime.records.relations.lookup import lookup_key


class Selector(Protocol):
    def select(self, record) -> List[Any]:
        return []


class PathSelector(Selector):
    def __init__(self, *paths):
        self.paths = [x.split(".") for x in paths]

    def select(self, record):
        ret = []
        for path in self.paths:
            for rec in getter(record, path):
                ret.append(rec)
        return ret


class FirstItemSelector(PathSelector):
    def select(self, record):
        for rec in super().select(record):
            return [rec]
        return []


@dataclasses.dataclass
class FilteredSelector(Selector):
    """
    Selector which filters output of another selector
    Example:
        FilteredSelector(PathSelector("metadata.creators", "metadata.contributors"),
                                         filter=lambda x: x["nameType"] == "personal", projection="affiliations")

    selects affiliations of creators with nameType personal from following data

    data = {
        "metadata": {
            "creators": [
                {"name": "hugo", "affiliations": ["uni1", "uni2"], "nameType": "personal"},
                {"name": "uni3", "nameType": "organizational"},
            ]
        }
    }
    """
    selector: Selector
    filter: Callable[[Any], bool]
    projection: Callable[[Any], Any] | str = None

    def select(self, record):
        selected = self.selector.select(record)
        selected = filter(self.filter, selected)
        if self.projection:
            ret = []
            for select_element in selected:
                if isinstance(self.projection, str):
                    result = [x.value for x in lookup_key(select_element, self.projection)]
                else:
                    result = self.projection(select_element)
                if isinstance(result, list):
                    ret += result
                else:
                    ret.append(result)
        else:
            ret = list(selected)
        return ret


@dataclasses.dataclass
class MultiSelector(Selector):
    """Selector concatenating outputs of multiple selectors"""

    def __init__(self, *selectors: Selector):
        self.selectors = selectors

    def select(self, record):
        ret = []
        for selector in self.selectors:
            ret += selector.select(record)
        return ret


def getter(data, path: List):
    if len(path) == 0:
        if isinstance(data, list):
            yield from data
        else:
            yield data
    elif isinstance(data, dict):
        if path[0] in data:
            yield from getter(data[path[0]], path[1:])
    elif isinstance(data, list):
        for item in data:
            yield from getter(item, path)