from flask_resources.responses import ResponseHandler

class ExportableResponseHandler(ResponseHandler):

    def __init__(self, serializer, export_code, name, headers=None):
        """Constructor."""
        self.export_code = export_code
        self.name = name
        super().__init__(serializer, headers)