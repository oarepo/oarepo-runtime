from .base import oarepo
import click
from flask import current_app
from flask.cli import with_appcontext
from importlib_metadata import entry_points
from collections import defaultdict
import json


@oarepo.group()
def assets():
    "OARepo asset addons"


@assets.command()
@click.argument("output_file")
@with_appcontext
@click.pass_context
def collect(ctx, output_file):
    deps = []
    theme = current_app.config["APP_THEME"] or "semantic-ui"

    for ep in entry_points(group="invenio_assets.webpack"):
        webpack = ep.load()
        if theme in webpack.themes:
            deps.append(webpack.themes[theme].path)
    with open(output_file, "w") as f:
        json.dump({"assets": deps}, f)
