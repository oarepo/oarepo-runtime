#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test signposting."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from oarepo_runtime.proxies import current_runtime
from oarepo_runtime.resources.signposting import (
    create_linkset,
    create_linkset_json,
    export_format_signpost_links_list,
    file_content_signpost_links_list,
    landing_page_signpost_links_list,
    list_of_signpost_links_to_http_header,
    record_dict_to_json_linkset,
    record_dict_to_linkset,
    signpost_link_to_str,
)
from oarepo_runtime.typing import record_from_result


# taken from https://github.com/inveniosoftware/invenio-records-resources/blob/master/tests/services/files/files_utils.py
def add_file_to_record(file_service, record_item_id, file_id, identity, data=None):
    """Add a file to the record."""
    file_service.init_files(identity, record_item_id, data=[{"key": file_id}])
    file_service.set_file_content(
        identity,
        record_item_id,
        file_id,
        BytesIO(data or (b"test file content: " + file_id.encode("utf-8"))),
    )
    return file_service.commit_file(identity, record_item_id, file_id)


def test_signposting_linkset(
    app_with_mock_ui_bp, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
    record_item = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "unknown": True,
            "files": {
                "enabled": True,
            },
        },
    )
    record = record_from_result(record_item)
    file_service = current_runtime.get_file_service_for_record(record)
    file_item = add_file_to_record(file_service, record_item.id, "test.png", identity_simple)

    record_item = service.read_draft(identity_simple, record_item.id, expand=True).to_dict()

    with (Path(__file__).parent / "data/datacite_export.json").open() as f:
        datacite_dict = json.load(f)
    signposting_links = landing_page_signpost_links_list(
        datacite_dict=datacite_dict, record_dict=record_item, short=True
    )
    signposting_linkset_json = create_linkset_json(datacite_dict=datacite_dict, record_dict=record_item)
    signposting_linkset = create_linkset(datacite_dict=datacite_dict, record_dict=record_item)
    record_id = record_item["id"]
    assert signposting_linkset_json == {
        "linkset": [
            {
                "anchor": f"https://127.0.0.1:5000/uploads/{record_id}",
                "author": [{"href": "https://orcid.org/0000-0001-5727-2427"}, {"href": "https://ror.org/04wxnsj81"}],
                "cite-as": [{"href": "https://doi.org/10.82433/b09z-4k37"}],
                "describedby": [
                    {
                        "href": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api",
                        "type": "application/json",
                    },
                    {
                        "href": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite",
                        "type": "application/vnd.datacite.datacite+json",
                    },
                ],
                "item": [
                    {
                        "href": f"https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/{file_item.file_id}",
                        "type": "image/png",
                    }
                ],
                "license": [{"href": "https://spdx.org/licenses/cc-by-4.0"}],
                "type": [{"href": "https://schema.org/Dataset"}, {"href": "https://schema.org/AboutPage"}],
            },
            {
                "anchor": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api",
                "describes": [{"href": f"https://127.0.0.1:5000/uploads/{record_id}", "type": "text/html"}],
            },
            {
                "anchor": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite",
                "describes": [{"href": f"https://127.0.0.1:5000/uploads/{record_id}", "type": "text/html"}],
            },
            {
                "anchor": f"https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/{file_item.file_id}",
                "collection": [{"href": f"https://127.0.0.1:5000/uploads/{record_id}", "type": "text/html"}],
            },
        ]
    }
    assert str(signposting_links) == (
        "[<Signpost rel=author target=https://orcid.org/0000-0001-5727-2427>, "
        "<Signpost rel=author target=https://ror.org/04wxnsj81>, <Signpost "
        "rel=cite-as target=https://doi.org/10.82433/b09z-4k37>, "
        "<Signpost rel=describedby "
        f"target=https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api "
        "type=application/json>, <Signpost rel=describedby "
        f"target=https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite "
        "type=application/vnd.datacite.datacite+json>, <Signpost rel=item "
        f"target=https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/{file_item.file_id} "
        "type=image/png>, <Signpost rel=license "
        "target=https://spdx.org/licenses/cc-by-4.0>, <Signpost rel=type "
        "target=https://schema.org/Dataset>, <Signpost rel=type "
        "target=https://schema.org/AboutPage>]"
    )
    assert signpost_link_to_str(signposting_links[0]) == "<https://orcid.org/0000-0001-5727-2427>; rel=author"

    assert signposting_linkset == (
        f'<https://orcid.org/0000-0001-5727-2427>; rel=author; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://ror.org/04wxnsj81>; rel=author; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://doi.org/10.82433/b09z-4k37>; rel=cite-as; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f"<https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api>; "
        f'rel=describedby; type="application/json"; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f"<https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite>; "
        'rel=describedby; type="application/vnd.datacite.datacite+json"; '
        f'anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f"<https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/{file_item.file_id}>; "
        f'rel=item; type="image/png"; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://spdx.org/licenses/cc-by-4.0>; rel=license; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://schema.org/Dataset>; rel=type; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://schema.org/AboutPage>; rel=type; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://127.0.0.1:5000/uploads/{record_id}>; rel=describes; type="text/html"; '
        f'anchor="https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api", '
        f'<https://127.0.0.1:5000/uploads/{record_id}>; rel=describes; type="text/html"; '
        f'anchor="https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite", '
        f'<https://127.0.0.1:5000/uploads/{record_id}>; rel=collection; type="text/html"; '
        f'anchor="https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/{file_item.file_id}"'
    )

    assert record_dict_to_linkset(record_item) == (
        f'<https://orcid.org/0000-0001-5727-2427>; rel=author; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://ror.org/04wxnsj81>; rel=author; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://doi.org/10.82433/b09z-4k37>; rel=cite-as; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f"<https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api>; rel=describedby; "
        f'type="application/json"; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f"<https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite>; rel=describedby; "
        f'type="application/vnd.datacite.datacite+json"; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/test.png>; rel=item; type="image/png"; '
        f'anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://spdx.org/licenses/cc-by-4.0>; rel=license; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://schema.org/Dataset>; rel=type; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://schema.org/AboutPage>; rel=type; anchor="https://127.0.0.1:5000/uploads/{record_id}", '
        f'<https://127.0.0.1:5000/uploads/{record_id}>; rel=describes; type="text/html"; '
        f'anchor="https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api", '
        f'<https://127.0.0.1:5000/uploads/{record_id}>; rel=describes; type="text/html"; '
        f'anchor="https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite", '
        f'<https://127.0.0.1:5000/uploads/{record_id}>; rel=collection; type="text/html"; '
        f'anchor="https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/test.png"'
    )
    assert record_dict_to_json_linkset(record_item) == {
        "linkset": [
            {
                "anchor": f"https://127.0.0.1:5000/uploads/{record_id}",
                "author": [{"href": "https://orcid.org/0000-0001-5727-2427"}, {"href": "https://ror.org/04wxnsj81"}],
                "cite-as": [{"href": "https://doi.org/10.82433/b09z-4k37"}],
                "describedby": [
                    {
                        "href": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api",
                        "type": "application/json",
                    },
                    {
                        "href": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite",
                        "type": "application/vnd.datacite.datacite+json",
                    },
                ],
                "item": [
                    {"href": f"https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/test.png", "type": "image/png"}
                ],
                "license": [{"href": "https://spdx.org/licenses/cc-by-4.0"}],
                "type": [{"href": "https://schema.org/Dataset"}, {"href": "https://schema.org/AboutPage"}],
            },
            {
                "anchor": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api",
                "describes": [{"href": f"https://127.0.0.1:5000/uploads/{record_id}", "type": "text/html"}],
            },
            {
                "anchor": f"https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite",
                "describes": [{"href": f"https://127.0.0.1:5000/uploads/{record_id}", "type": "text/html"}],
            },
            {
                "anchor": f"https://127.0.0.1:5000/api/mocks/{record_id}/draft/files/test.png",
                "collection": [{"href": f"https://127.0.0.1:5000/uploads/{record_id}", "type": "text/html"}],
            },
        ]
    }
    model = current_runtime.get_model_for_record(record)
    model_exports = model.exports
    model._exports = []  # noqa: SLF001
    assert record_dict_to_json_linkset(record_item) == {}
    assert record_dict_to_linkset(record_item) == ""
    model._exports = model_exports  # noqa: SLF001


def test_files_signposting(
    app_with_mock_ui_bp, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
    record_item = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "unknown": True,
            "files": {
                "enabled": True,
            },
        },
    ).to_dict()
    file_content_signposting = file_content_signpost_links_list(record_dict=record_item)
    record_id = record_item["id"]
    assert str(file_content_signposting) == (
        "[<Signpost rel=linkset "
        f"target=https://127.0.0.1:5000/api/test-ui-links/records/{record_id} "
        "type=application/linkset>, <Signpost rel=linkset "
        f"target=https://127.0.0.1:5000/api/test-ui-links/records/{record_id} "
        "type=application/linkset+json>, <Signpost rel=collection "
        f"target=https://127.0.0.1:5000/api/test-ui-links/records/{record_id} "
        "type=text/html>]"
    )


def test_export_format_signposting(
    app_with_mock_ui_bp, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
    record_item = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "unknown": True,
            "files": {
                "enabled": True,
            },
        },
    ).to_dict()
    export_format_signposting = export_format_signpost_links_list(record_dict=record_item)
    record_id = record_item["id"]
    assert str(export_format_signposting) == (
        f"[<Signpost rel=linkset target=https://127.0.0.1:5000/uploads/{record_id} "
        "type=application/linkset>, <Signpost rel=linkset "
        f"target=https://127.0.0.1:5000/uploads/{record_id} "
        "type=application/linkset+json>, <Signpost rel=describes "
        f"target=https://127.0.0.1:5000/uploads/{record_id} type=text/html>]"
    )


def test_landing_page_signposting(
    app_with_mock_ui_bp, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
    record_item = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "unknown": True,
            "files": {
                "enabled": True,
            },
        },
    ).to_dict()
    with (Path(__file__).parent / "data/datacite_export.json").open() as f:
        datacite_dict = json.load(f)
    landing_page_signposting = landing_page_signpost_links_list(
        datacite_dict=datacite_dict, record_dict=record_item, short=True
    )
    record_id = record_item["id"]
    assert str(landing_page_signposting) == (
        "[<Signpost rel=author target=https://orcid.org/0000-0001-5727-2427>, "
        "<Signpost rel=author target=https://ror.org/04wxnsj81>, "
        "<Signpost rel=cite-as target=https://doi.org/10.82433/b09z-4k37>, "
        "<Signpost rel=describedby "
        f"target=https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api "
        "type=application/json>, "
        "<Signpost rel=describedby "
        f"target=https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite "
        "type=application/vnd.datacite.datacite+json>, "
        "<Signpost rel=license target=https://spdx.org/licenses/cc-by-4.0>, "
        "<Signpost rel=type target=https://schema.org/Dataset>, "
        "<Signpost rel=type target=https://schema.org/AboutPage>]"
    )


def test_create_signposting_header(
    app_with_mock_ui_bp, db, search_with_field_mapping, service, search_clear, identity_simple, location
):
    record_item = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "Test Record"},
            "unknown": True,
            "files": {
                "enabled": True,
            },
        },
    ).to_dict()
    with (Path(__file__).parent / "data/datacite_export.json").open() as f:
        datacite_dict = json.load(f)
    signposting_links = landing_page_signpost_links_list(
        datacite_dict=datacite_dict, record_dict=record_item, short=True
    )
    signposting_header = list_of_signpost_links_to_http_header(links_list=signposting_links)
    record_id = record_item["id"]
    assert signposting_header == (
        "Link: <https://orcid.org/0000-0001-5727-2427>; rel=author, "
        "<https://ror.org/04wxnsj81>; rel=author, "
        "<https://doi.org/10.82433/b09z-4k37>; rel=cite-as, "
        f"<https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/mock-api>; "
        'rel=describedby; type="application/json", '
        f"<https://127.0.0.1:5000/api/test-ui-links/records/{record_id}/export/datacite>; "
        'rel=describedby; type="application/vnd.datacite.datacite+json", '
        "<https://spdx.org/licenses/cc-by-4.0>; rel=license, "
        "<https://schema.org/Dataset>; rel=type, <https://schema.org/AboutPage>; "
        "rel=type"
    )
