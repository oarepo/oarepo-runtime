from contextvars import ContextVar

from flask import current_app
from werkzeug.local import LocalProxy

current_timezone = ContextVar(
    "timezone"
)  # idk how or exactly why to use the LocalProxy here
current_datastreams = LocalProxy(lambda: current_app.extensions["oarepo-datastreams"])
current_oarepo = LocalProxy(lambda: current_app.extensions["oarepo-runtime"])
"""Helper proxy to get the current datastreams."""
