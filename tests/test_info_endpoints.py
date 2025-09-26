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

    assert models_info == [
        {
            "content_types": [
                {
                    "can_deposit": True,
                    "can_export": True,
                    "code": "mock-api",
                    "content_type": "application/json",
                    "description": "Test description",
                    "name": "Test",
                    "schema": "https://127.0.0.1:5000/.well-known/repository/schema/records/record-v1.0.0.json",
                }
            ],
            "description": None,
            "features": ["requests", "drafts", "files"],
            "links": {
                "deposit": "https://127.0.0.1:5000/api/mocks?type=mocks&_external=True",
                "drafts": None,
                "html": "https://127.0.0.1:5000/mocks",
                "records": "https://127.0.0.1:5000/api/mocks?type=mocks&_external=True",
            },
            "metadata": True,
            "name": "mock",
            "schema": "local://records/record-v1.0.0.json",
            "type": "mock",
            "version": "1.0.0",
        },
        {
            "content_types": [
                {
                    "can_deposit": False,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Trueaffiliations/affiliation-v1.0.0.json",
                }
            ],
            "description": "",
            "features": ["rdm", "vocabulary"],
            "links": {"records": "https://127.0.0.1:5000/?_external=True/api/affiliations"},
            "metadata": False,
            "name": "Affiliations",
            "schema": "local://affiliations/affiliation-v1.0.0.json",
            "type": "affiliations",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": False,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Trueawards/award-v1.0.0.json",
                }
            ],
            "description": "",
            "features": ["rdm", "vocabulary"],
            "links": {"records": "https://127.0.0.1:5000/?_external=True/api/awards"},
            "metadata": False,
            "name": "Awards",
            "schema": "local://awards/award-v1.0.0.json",
            "type": "awards",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": False,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Truefunders/funder-v1.0.0.json",
                }
            ],
            "description": "",
            "features": ["rdm", "vocabulary"],
            "links": {"records": "https://127.0.0.1:5000/?_external=True/api/funders"},
            "metadata": False,
            "name": "Funders",
            "schema": "local://funders/funder-v1.0.0.json",
            "type": "funders",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": False,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Truesubjects/subject-v1.0.0.json",
                }
            ],
            "description": "",
            "features": ["rdm", "vocabulary"],
            "links": {"records": "https://127.0.0.1:5000/?_external=True/api/subjects"},
            "metadata": False,
            "name": "Subjects",
            "schema": "local://subjects/subject-v1.0.0.json",
            "type": "subjects",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": False,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Truenames/name-v1.0.0.json",
                }
            ],
            "description": "",
            "features": ["rdm", "vocabulary"],
            "links": {"records": "https://127.0.0.1:5000/?_external=True/api/names"},
            "metadata": False,
            "name": "Names",
            "schema": "local://names/name-v1.0.0.json",
            "type": "names",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": True,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Trueaffiliations/affiliation-v1.0.0.json",
                }
            ],
            "description": "Specialized vocabulary for affiliations",
            "features": ["rdm", "vocabulary"],
            "links": {
                "deposit": "https://127.0.0.1:5000/?_external=True/api/vocabularies/affiliations-vocab",
                "records": "https://127.0.0.1:5000/?_external=True/api/vocabularies/affiliations-vocab",
            },
            "metadata": False,
            "name": "Affiliations",
            "schema": "local://affiliations/affiliation-v1.0.0.json",
            "type": "affiliations-vocab",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": True,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Trueawards/award-v1.0.0.json",
                }
            ],
            "description": "Specialized vocabulary for awards",
            "features": ["rdm", "vocabulary"],
            "links": {
                "deposit": "https://127.0.0.1:5000/?_external=True/api/vocabularies/awards-vocab",
                "records": "https://127.0.0.1:5000/?_external=True/api/vocabularies/awards-vocab",
            },
            "metadata": False,
            "name": "Awards",
            "schema": "local://awards/award-v1.0.0.json",
            "type": "awards-vocab",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": True,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Truefunders/funder-v1.0.0.json",
                }
            ],
            "description": "Specialized vocabulary for funders",
            "features": ["rdm", "vocabulary"],
            "links": {
                "deposit": "https://127.0.0.1:5000/?_external=True/api/vocabularies/funders-vocab",
                "records": "https://127.0.0.1:5000/?_external=True/api/vocabularies/funders-vocab",
            },
            "metadata": False,
            "name": "Funders",
            "schema": "local://funders/funder-v1.0.0.json",
            "type": "funders-vocab",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": True,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Truesubjects/subject-v1.0.0.json",
                }
            ],
            "description": "Specialized vocabulary for subjects",
            "features": ["rdm", "vocabulary"],
            "links": {
                "deposit": "https://127.0.0.1:5000/?_external=True/api/vocabularies/subjects-vocab",
                "records": "https://127.0.0.1:5000/?_external=True/api/vocabularies/subjects-vocab",
            },
            "metadata": False,
            "name": "Subjects",
            "schema": "local://subjects/subject-v1.0.0.json",
            "type": "subjects-vocab",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": True,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Truenames/name-v1.0.0.json",
                }
            ],
            "description": "Specialized vocabulary for names",
            "features": ["rdm", "vocabulary"],
            "links": {
                "deposit": "https://127.0.0.1:5000/?_external=True/api/vocabularies/names-vocab",
                "records": "https://127.0.0.1:5000/?_external=True/api/vocabularies/names-vocab",
            },
            "metadata": False,
            "name": "Names",
            "schema": "local://names/name-v1.0.0.json",
            "type": "names-vocab",
            "version": "unknown",
        },
        {
            "content_types": [
                {
                    "can_deposit": True,
                    "can_export": True,
                    "content_type": "application/json",
                    "description": "Vocabulary JSON",
                    "name": "Invenio RDM JSON",
                    "schema": "https://127.0.0.1:5000/?_external=Truevocabularies/vocabulary-v1.0.0.json",
                }
            ],
            "description": "",
            "features": ["rdm", "vocabulary"],
            "links": {
                "deposit": "https://127.0.0.1:5000/?_external=True/api/vocabularies/languages",
                "records": "https://127.0.0.1:5000/?_external=True/api/vocabularies/languages",
            },
            "metadata": False,
            "name": "languages",
            "schema": "local://vocabularies/vocabulary-v1.0.0.json",
            "type": "languages",
            "version": "unknown",
        },
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
