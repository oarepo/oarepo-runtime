from functools import cached_property

import pytz
from flask import current_app, session
from invenio_accounts.models import User
from invenio_base.utils import obj_or_import_string

from .cli import oarepo as oarepo_cmd
from .datastreams.ext import OARepoDataStreamsExt
from .proxies import current_timezone


def set_timezone():
    if "timezone" in session:
        current_timezone.set(pytz.timezone(session["timezone"]))
    else:
        default_user_timezone = current_app.config.get("BABEL_DEFAULT_TIMEZONE")
        if default_user_timezone:
            current_timezone.set(pytz.timezone(default_user_timezone))
        else:
            current_timezone.set(None)


def on_identity_changed(sender, identity):
    if "timezone" not in session and "_user_id" in session:
        user = User.query.filter_by(id=session["_user_id"]).first()
        if user and "timezone" in user.preferences:
            session["timezone"] = user.preferences["timezone"]
    set_timezone()

timezone = ContextVar('timezone')
def on_identity_changed(sender, identity):
    if "timezone" not in session:
        user = UserAggregate.get_record(session["_user_id"])
        if "timezone" in user.preferences:
            session["timezone"] = user.preferences["timezone"]

class OARepoRuntime(object):
    """OARepo extension of Invenio-Vocabularies."""

    def __init__(self, app=None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app):
        """Flask application initialization."""
        self.init_config(app)
        self.app = app
        app.extensions["oarepo-runtime"] = self
        app.extensions["oarepo-datastreams"] = OARepoDataStreamsExt(app)
        app.cli.add_command(oarepo_cmd)

        from flask_principal import identity_changed

        identity_changed.connect(on_identity_changed, self.app)
        app.before_request(set_timezone)

    @cached_property
    def owner_entity_resolvers(self):
        return [
            obj_or_import_string(x) for x in self.app.config["OWNER_ENTITY_RESOLVERS"]
        ]

    @cached_property
    def rdm_excluded_components(self):
        return [
            obj_or_import_string(x)
            for x in self.app.config.get("RDM_EXCLUDED_COMPONENTS", [])
        ]

    def init_config(self, app):
        """Initialize configuration."""
        from . import ext_config

        if "OAREPO_PERMISSIONS_PRESETS" not in app.config:
            app.config["OAREPO_PERMISSIONS_PRESETS"] = {}

        for k in ext_config.OAREPO_PERMISSIONS_PRESETS:
            if k not in app.config["OAREPO_PERMISSIONS_PRESETS"]:
                app.config["OAREPO_PERMISSIONS_PRESETS"][k] = (
                    ext_config.OAREPO_PERMISSIONS_PRESETS[k]
                )

        for k in dir(ext_config):
            if k == "DEFAULT_DATASTREAMS_EXCLUDES":
                app.config.setdefault(k, []).extend(getattr(ext_config, k))

            elif k.startswith("DATASTREAMS_"):
                val = getattr(ext_config, k)
                if isinstance(val, dict):
                    self.add_non_existing(app.config.setdefault(k, {}), val)
                else:
                    app.config.setdefault(k, val)

            elif k == "HAS_DRAFT_CUSTOM_FIELD":
                app.config.setdefault(k, getattr(ext_config, k))

            elif k == "OAREPO_FACET_GROUP_NAME":
                app.config.setdefault(k, getattr(ext_config, k))

            elif k == "OWNER_ENTITY_RESOLVERS":
                app.config.setdefault(k, []).extend(getattr(ext_config, k))

    def add_non_existing(self, target, source):
        for val_k, val_value in source.items():
            if val_k not in target:
                target[val_k] = val_value
