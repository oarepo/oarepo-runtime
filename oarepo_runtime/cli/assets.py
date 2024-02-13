import json
import os
import re
from pathlib import Path

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
@click.option("--repository-dir")
@click.option("--assets-dir", default=".assets")
@with_appcontext
def collect(output_file, repository_dir, assets_dir):
    aliases, asset_dirs = enumerate_assets()

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

    root_aliases = {}
    asset_paths = [Path(x) for x in asset_dirs]
    for alias, path in aliases.items():
        for pth in asset_paths:
            possible_path = pth / path
            if possible_path.exists():
                try:
                    relative_path = str(
                        possible_path.relative_to(repository_dir or os.getcwd())
                    )
                    root_aliases[alias] = "./" + relative_path
                except ValueError:
                    root_aliases[alias] = str(Path(assets_dir) / path)

    with open(output_file, "w") as f:
        json.dump(
            {
                "assets": asset_dirs,
                "static": static_deps,
                "@aliases": aliases,
                "@root_aliases": root_aliases,
            },
            f,
            indent=4,
            ensure_ascii=False,
        )


def enumerate_assets():
    asset_dirs = []
    aliases = {}
    theme = (current_app.config["APP_THEME"] or ["semantic-ui"])[0]
    for ep in entry_points(group="invenio_assets.webpack"):
        webpack = ep.load()
        if theme in webpack.themes:
            asset_dirs.append(webpack.themes[theme].path)
            aliases.update(webpack.themes[theme].aliases)
    return aliases, asset_dirs


COMPONENT_RE = re.compile(
    r"""
^
\s*
&        # start of import statement & { import "blah"; }
\s*
{    
\s*
@import\s+["'](.*?)["']
\s*
;
\s*
}""",
    re.MULTILINE | re.DOTALL | re.VERBOSE,
)


@assets.command(name="less-components")
@click.argument("output_file", default="-")
@with_appcontext
def less_components(output_file):
    aliases, asset_dirs = enumerate_assets()
    asset_dirs = [Path(x) for x in asset_dirs]
    less_component_files = []
    for asset_dir in asset_dirs:
        less_dir = asset_dir / "less"
        if less_dir.exists():
            for f in less_dir.glob("**/custom-components.less"):
                less_component_files.append(f)
    components = set()
    for cmp_file in less_component_files:
        for s in COMPONENT_RE.findall(cmp_file.read_text()):
            components.add(Path(s).stem)
    data = {"components": list(sorted(components))}
    if output_file == "-":
        print(json.dumps(data, indent=4, ensure_ascii=False))
    else:
        with open(output_file, "w") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
