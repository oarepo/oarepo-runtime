import functools

from invenio_base.utils import obj_or_import_string

from oarepo_runtime.datastreams.datastreams import Signature


class OARepoDataStreamsExt:
    def __init__(self, app):
        self.app = app

    def get_reader(self, reader, identity, **kwargs):
        return self._get_instance("DATASTREAMS_READERS", identity, kwargs, reader)

    def get_writer(self, writer, identity, **kwargs):
        return self._get_instance("DATASTREAMS_WRITERS", identity, kwargs, writer)

    def get_transformer(self, transformer, identity, **kwargs):
        return self._get_instance(
            "DATASTREAMS_TRANSFORMERS", identity, kwargs, transformer
        )

    def _get_instance(self, config_name, identity, kwargs, inst):
        if isinstance(inst, Signature):
            config_classes = self._get_classes_from_config(config_name)
            if inst.name not in config_classes:
                raise KeyError(f"'{inst.name}' not found in config {config_name}")
            reader_class = config_classes[inst.name]
            return reader_class(**(inst.kwargs or {}), **kwargs, identity=identity)
        else:
            return inst

    @functools.lru_cache(maxsize=5)
    def _get_classes_from_config(self, config_name):
        return {
            class_key: obj_or_import_string(class_name)
            for class_key, class_name in self.app.config[config_name].items()
        }
