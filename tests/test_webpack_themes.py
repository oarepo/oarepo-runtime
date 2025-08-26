from oarepo_runtime.cli.assets import enumerate_assets


def test_webpack_themes(ui_app):
    with ui_app.app_context():
        aliases, asset_dirs, generated_paths = enumerate_assets()
        assert "@translations/invenio_administration" in aliases
        assert generated_paths == []
