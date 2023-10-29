from invenio_records.dumpers import SearchDumperExt
from sqlalchemy.util import classproperty

from oarepo_runtime.utils.path import PathTraversal


class EDTFIntervalDumperExt(SearchDumperExt):
    paths = []
    _path_traversal = None

    @classproperty
    def path_traversal(cls):
        if cls._path_traversal is None:
            cls._path_traversal = PathTraversal(cls.paths)
        return cls._path_traversal

    def dump(self, record, data):
        for path in self.path_traversal.iter(data):
            rec = path[-1].current
            rec = rec.split("/")
            search_range = {}
            if rec[0]:
                search_range["gte"] = rec[0]
            if rec[1]:
                search_range["lte"] = rec[1]
            path[-1].parent_data[path[-1].key] = search_range
        return data

    def load(self, data, record_cls):
        for path in self.path_traversal.iter(data):
            rec = path[-1].current
            if rec:
                path[-1].parent_data[
                    path[-1].key
                ] = f"{rec.get('gte', '')}/{rec.get('lte', '')}"
            else:
                del path[-1].parent_data[path[-1].key]
        return data
