import json
import os

import click
from flask import current_app
from flask.cli import with_appcontext
from importlib_metadata import entry_points

from .base import oarepo


@oarepo.group()
def assets():
    "OARepo asset addons"


@assets.command()
@click.argument("output_file")
@with_appcontext
def collect(output_file):
    asset_deps = []
    theme = (current_app.config["APP_THEME"] or ["semantic-ui"])[0]

    for ep in entry_points(group="invenio_assets.webpack"):
        webpack = ep.load()
        if theme in webpack.themes:
            asset_deps.append(webpack.themes[theme].path)

    app_and_blueprints = [current_app] + list(current_app.blueprints.values())

    static_deps = []
    instance_path = current_app.instance_path
    if instance_path[-1] != "/":
        instance_path += "/"

    for bp in app_and_blueprints:
        if (
            bp.has_static_folder
            and os.path.isdir(bp.static_folder)
            and not bp.static_folder.startswith(instance_path)
        ):
            static_deps.append(bp.static_folder)

    with open(output_file, "w") as f:
        json.dump({"assets": asset_deps, "static": static_deps}, f)


@assets.command(name="less-components")
@click.argument("output_file")
@with_appcontext
def less_components(output_file):
    with open(output_file, "w") as f:
        json.dump(
            {"components": current_app.config.get("OAREPO_UI_LESS_COMPONENTS", [])}, f
        )
