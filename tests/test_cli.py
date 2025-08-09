from invenio_search.cli import destroy

from oarepo_runtime.cli.search import init


def test_cli(app, search):
    """Test CLI commands."""
    runner = app.test_cli_runner()
    result = runner.invoke(destroy, "--yes-i-know")
    result = runner.invoke(init)
    assert result.exit_code == 0
