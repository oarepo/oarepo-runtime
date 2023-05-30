from invenio_records.dumpers import SearchDumperExt
from sqlalchemy.util import classproperty

from oarepo_runtime.utils.path import PathTraversal


class MultilingualDumper(SearchDumperExt):
    paths = []
    SUPPORTED_LANGS = []
    _path_traversal = None

    @classproperty
    def path_traversal(cls):
        if cls._path_traversal is None:
            cls._path_traversal = PathTraversal(cls.paths)
        return cls._path_traversal

    def dump(self, record, data):
        for path in self.path_traversal.iter(data):
            rec = path[-1].current
            if rec["lang"] in self.SUPPORTED_LANGS:
                el_name = path[-1].key + "_" + rec["lang"]
                path[-1].parent_data.setdefault(el_name, []).append(rec["value"])
        return data

    def load(self, data, record_cls):
        for path in self.path_traversal.iter(data):
            rec = path[-1].current
            if rec["lang"] in self.SUPPORTED_LANGS:
                el_name = path[-1].key + "_" + rec["lang"]
                path[-1].parent_data.pop(el_name, None)
        return data
