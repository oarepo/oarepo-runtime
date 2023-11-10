from flask import current_app
from werkzeug.local import LocalProxy

current_datastreams = LocalProxy(lambda: current_app.extensions["oarepo-datastreams"])
"""Helper proxy to get the current datastreams."""
