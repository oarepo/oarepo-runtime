import json

import click
import importlib_metadata


@click.group()
def oarepo():
    """OARepo commands."""


def as_command(group, name, *args):
    args = [group.command(name=name), *args]
    actual = args[-1]
    for arg in reversed(args[:-1]):
        actual = arg(actual)
    return actual


@oarepo.command(name="version")
def get_version():
    versions = {}
    for distro in importlib_metadata.distributions():
        versions[distro.metadata["Name"]] = distro.version
    print(json.dumps(versions, ensure_ascii=False, indent=4))
