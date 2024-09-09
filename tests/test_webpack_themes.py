from oarepo_runtime.cli.assets import enumerate_assets


def test_webpack_themes(app):
    enumerated = enumerate_assets()
    assert '@translations/invenio_administration' in enumerated[0]