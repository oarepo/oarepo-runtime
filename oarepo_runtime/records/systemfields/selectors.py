from typing import List


class Selector:
    def select(self, record):
        return []


class PathSelector:
    def __init__(self, *paths, max_count=None):
        self.paths = [x.split('.') for x in paths]
        self.max_count = max_count

    def select(self, record):
        ret = []
        for path in self.paths:
            for rec in getter(record, path):
                ret.append(rec)
                if len(ret) == self.max_count:
                    return ret
        return ret

class LanguageSelector(PathSelector):
    def __init__(self, ):
        pass
def getter(data, path: List):
    if len(path) == 0:
        yield data
    elif isinstance(data, dict):
        if path[0] in data:
            yield from getter(data[path[0]], path[1:])
    elif isinstance(data, list):
        for item in data:
            yield from getter(item, path)

