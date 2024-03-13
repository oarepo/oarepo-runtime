from typing import List


class Selector:
    def select(self, record):
        return []


class PathSelector:
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
