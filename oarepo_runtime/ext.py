class OARepoRuntime(object):
    """OARepo base of invenio oarepo client."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.app = app
        app.extensions["oarepo-runtime"] = self