import functools

from invenio_base.utils import obj_or_import_string

from oarepo_runtime.datastreams.datastreams import Signature


class OARepoDataStreamsExt:
    def __init__(self, app):
        self.app = app

    def get_reader(self, reader):
        if isinstance(reader, Signature):
            reader_class = self._get_class("DATASTREAMS_READERS", reader.name)
            return reader_class(**(reader.kwargs or {}))
        else:
            return reader

    def get_writer(self, writer, **kwargs):
        if isinstance(writer, Signature):
            writer_class = self._get_class("DATASTREAMS_WRITERS", writer.name)
            return writer_class(**(writer.kwargs or {}), **kwargs)
        return writer

    def get_transformer(self, transformer, **kwargs):
        if isinstance(transformer, Signature):
            transformer_class = self._get_class(
                "DATASTREAMS_TRANSFORMERS", transformer.name
            )
            return transformer_class(**(transformer.kwargs or {}), **kwargs)
        return transformer

    def _get_class(self, config_name, name):
        config_classes = self._get_classes_from_config(config_name)
        if name in config_classes:
            return config_classes[name]
        raise KeyError(f"'{name}' not found in config {config_name}")

    @functools.lru_cache(maxsize=5)
    def _get_classes_from_config(self, config_name):
        return {
            class_key: obj_or_import_string(class_name)
            for class_key, class_name in self.app.config[config_name].items()
        }
