import oarepo_runtime.cf.cli  # noqa, just to register
import oarepo_runtime.datastreams.cli  # noqa, just to register

from .cli import oarepo as oarepo_cmd


class OARepoRuntime(object):
    """OARepo extension of Invenio-Vocabularies."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        app.extensions["oarepo-runtime"] = self
        app.cli.add_command(oarepo_cmd)

    def init_config(self, app):
        """Initialize configuration."""
        from . import ext_config

        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][
                    k
                ] = ext_config.OAREPO_PERMISSIONS_PRESETS[k]

        for k in dir(ext_config):
            if k == "DEFAULT_DATASTREAMS_EXCLUDES":
                app.config.setdefault(k, []).extend(getattr(ext_config, k))

            elif k.startswith("DEFAULT_DATASTREAMS_"):
                app.config.setdefault(k, {}).update(getattr(ext_config, k))

            elif k.startswith("DATASTREAMS_"):
                app.config.setdefault(k, getattr(ext_config, k))
