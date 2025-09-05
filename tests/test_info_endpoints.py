def test_info_endpoint(client_with_credentials_admin, info_blueprint):
    repository_info = client_with_credentials_admin.get("/.well-known/repository/").json
    # remove rest of links
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
        "invenio_version": repository_info["invenio_version"],
        "transfers": ["L", "F", "R", "M"],
        "links": {
            "self": "https://127.0.0.1:5000/.well-known/repository/",
            "api": "https://127.0.0.1:5000/api",
            "models": "https://127.0.0.1:5000/.well-known/repository/models",
            "requests": "https://127.0.0.1:5000/requests/",
        },
        "features": ["drafts", "requests", "communities"],
    }
