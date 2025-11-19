#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
from __future__ import annotations

from packaging.version import Version

from oarepo_runtime.info.views import to_current_language


def test_info_repository_endpoint(client, lang_type, info_blueprint):
    repository_info = client.get("/.well-known/repository/").json
    models_info = client.get("/.well-known/repository/models").json
    schema_info = client.get("/.well-known/repository/schema/requests/request-v1.0.0.json").json

    # remove rest of links
    repository_info["links"] = {
        "self": repository_info["links"]["self"],
        "api": repository_info["links"]["api"],
        "models": repository_info["links"]["models"],
        "requests": repository_info["links"]["requests"],
    }

    assert repository_info["links"] == {
        "api": "https://127.0.0.1:5000/api",
        "models": "https://127.0.0.1:5000/.well-known/repository/models",
        "requests": "https://127.0.0.1:5000/api/requests/",
        "self": "https://127.0.0.1:5000/.well-known/repository/",
    }

    assert repository_info["features"] == ["drafts", "requests", "communities"]
    assert Version(repository_info["invenio_version"]) >= Version("13.0.14")
    assert repository_info["transfers"] == ["L", "F", "R", "M"]
    assert repository_info["version"] == "local development"
    assert repository_info["schema"] == "local://introspection-v1.0.0"
    assert repository_info["default_model"] == "mock"
    assert repository_info["test_info"] == "test"  # check that the component from conftest is used

    mock_model = next((model_dict for model_dict in models_info if model_dict["name"] == "mock"), None)
    mock_datacite_export = {
        "can_deposit": False,
        "can_export": True,
        "code": "datacite",
        "content_type": "application/vnd.datacite.datacite+json",
        "description": "Test description",
        "name": "Test",
    }
    assert mock_datacite_export in mock_model["content_types"]
    assert mock_model["features"] == ["requests", "drafts", "files"]
    assert mock_model["description"] is None
    assert mock_model["type"] == "mock"
    assert mock_model["metadata"]
    assert mock_model["version"] == "1.0.0"
    assert mock_model["links"] == {
        "deposit": "https://127.0.0.1:5000/api/mocks?type=mocks&_external=True",
        "drafts": None,
        "html": "https://127.0.0.1:5000/mocks",
        "records": "https://127.0.0.1:5000/api/mocks?type=mocks&_external=True",
    }

    model_names = [model_dict["name"] for model_dict in models_info]
    assert model_names == [
        "mock",
        "Affiliations",
        "Awards",
        "Funders",
        "Subjects",
        "Names",
        "Affiliations",
        "Awards",
        "Funders",
        "Subjects",
        "Names",
        "languages",
    ]

    assert schema_info["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema_info["$id"] == "local://requests/request-v1.0.0.json"
    assert schema_info["type"] == "object"
    assert not schema_info["additionalProperties"]
    assert schema_info["properties"]["$schema"] == {"$ref": "local://definitions-v1.0.0.json#/$schema"}
    assert schema_info["properties"]["id"] == {"$ref": "local://definitions-v1.0.0.json#/identifier"}
    assert schema_info["properties"]["type"] == {"type": "string"}
    assert schema_info["properties"]["title"] == {"type": "string"}
    assert schema_info["properties"]["description"] == {"type": "string"}
    assert schema_info["properties"]["status"] == {"type": "string"}
    assert schema_info["properties"]["payload"] == {"$ref": "local://requests/definitions-v1.0.0.json#/anything"}
    assert schema_info["properties"]["topic"] == {"$ref": "local://definitions-v1.0.0.json#/entity_reference"}
    assert schema_info["properties"]["receiver"] == {"$ref": "local://definitions-v1.0.0.json#/entity_reference"}
    assert schema_info["properties"]["created_by"] == {"$ref": "local://definitions-v1.0.0.json#/entity_reference"}
    assert schema_info["properties"]["@v"] == {"type": "string"}


def test_info_to_current_language_fn():
    assert to_current_language({"en": "test"}) == "test"

    assert to_current_language("not a dictionary") == "not a dictionary"
