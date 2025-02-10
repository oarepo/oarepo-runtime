def test_info_endpoint(client_with_credentials_admin, info_blueprint):
    repository_info = client_with_credentials_admin.get("/.well-known/repository/").json
    repository_info["links"] = {
        "self": repository_info["links"]["self"],
        "api": repository_info["links"]["api"],
        "models": repository_info["links"]["models"],
        "requests": repository_info["links"]["requests"],
    }
    assert repository_info == {
        "schema": "local://introspection-v1.0.0",
        "name": "",
        "description": "",
        "version": "local development",
        "invenio_version": "12.2.5",
        "transfers": ["L", "F", "R", "M"],
        "links": {
            "self": "http://localhost/.well-known/repository/",
            "api": "http://localhost/api",
            "models": "http://localhost/.well-known/repository/models",
            "requests": "http://localhost/requests/",
        },
        "features": ["drafts", "requests", "communities"],
    }
