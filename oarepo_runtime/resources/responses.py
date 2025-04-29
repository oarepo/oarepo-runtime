from flask_resources.responses import ResponseHandler

class ExportableResponseHandler(ResponseHandler):

    def __init__(self, serializer, export_code, name, headers=None):
        """Constructor."""
        self.export_code = export_code
        self.name = name
        super().__init__(serializer, headers)


class OAIExportableResponseHandler(ExportableResponseHandler):

    def __init__(self, serializer, export_code, name, oai_metadata_prefix, oai_schema, oai_namespace,
                 headers=None):
        """Constructor."""
        self.oai_metadata_prefix = oai_metadata_prefix
        self.oai_schema = oai_schema
        self.oai_namespace = oai_namespace
        super().__init__(serializer, export_code, name, headers)