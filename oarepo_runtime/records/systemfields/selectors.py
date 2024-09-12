from typing import Any, Callable, List


class Selector:
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

    def __init__(
        self,
        selector: Selector,
        filter: Callable[[Any], bool],
        projection: Callable[[Any], Any] | str = None,
    ):

        self.selector = selector
        self.filter = filter
        self.projection = projection

    def select(self, record):
        selected = self.selector.select(record)
        selected = filter(self.filter, selected)
        if self.projection:
            ret = []
            for select_element in selected:
                if isinstance(self.projection, str):
                    result = select_element[self.projection]
                else:
                    result = self.projection(select_element)
                if isinstance(result, list):
                    ret += result
                else:
                    ret.append(result)
        else:
            ret = list(selected)
        return ret


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


"""
def separate_element_condition(element):
    if "?" in element:
        return element.split("?")
    return element, None


def check(data, condition):
    if condition:
        key, value = condition.split("=")
        return key in data and data[key] == value
    else:
        return True


def getter(data, path: List, condition=None):
    # allows selection from list of dicts based on one of the dict's values
    if len(path) == 0:
        if isinstance(data, list):
            for item in data:
                if check(item, condition):
                    yield item
        elif isinstance(data, dict):
            if check(data, condition):
                yield data
        else:
            yield data

    elif isinstance(data, dict):
        element, condition = separate_element_condition(path[0])
        if element and element in data:
            next = data[element]
            if isinstance(next, list):
                yield from getter(next, path[1:], condition)
            elif isinstance(next, dict):
                if check(data, condition):
                    yield from getter(next, path[1:], None)

    elif isinstance(data, list):
        for item in data:
            if check(item, condition):
                yield from getter(item, path)
"""
