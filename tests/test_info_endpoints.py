def test_info_endpoint(
    client_with_credentials_admin,
    info_blueprint
):
    repository_info = client_with_credentials_admin.get("/.well-known/repository/").json
    assert repository_info == {
        'description': '',
        'invenio_version': '12.0.21',
        'links': {
            'models': 'http://localhost/.well-known/repository/models',
            'requests': 'http://localhost/requests/',
            'self': 'http://localhost/.well-known/repository/'
        },
        'name': '',
        'transfers': ['local-file', 'url-fetch'],
        'version': "local development"
    }
