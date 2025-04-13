from flask_resources.responses import ResponseHandler

class ExportableResponseHandler(ResponseHandler):

    def __init__(self, serializer, export_code, name, headers=None):
        """Constructor."""
        self.export_code = export_code
        self.name = name
        super().__init__(serializer, headers)


class OAIExportableResponseHandler(ExportableResponseHandler):

    def __init__(self, serializer, export_code, name, oai_code, oai_schema, oai_namespace, oai_serializer, headers=None):
        """Constructor."""
        self.oai_code = oai_code
        self.oai_schema = oai_schema
        self.oai_namespace = oai_namespace
        self.oai_serializer = oai_serializer
        super().__init__(serializer, export_code, name, headers)