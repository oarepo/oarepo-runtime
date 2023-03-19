import click


@click.group()
def oarepo():
    """OARepo commands."""


def as_command(group, name, *args):
    args = [group.command(name=name), *args]
    actual = args[-1]
    for arg in reversed(args[:-1]):
        actual = arg(actual)
    return actual
