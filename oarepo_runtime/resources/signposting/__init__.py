#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Signposting functionality.

Functions to create a list of signpost links record's landing page, export formats and file contents.
Separate functions to create a complete linkset for the record item in application/linkset or application/linkset+json format.
Function to format the linkset into a HTTP Link header.

Information about relation types can be found at: https://signposting.org/FAIR/#reltypes
Excerpt with explanations about relation types:
author 	        = The target of the link is a URI for an author of the resource that is the origin of the link.
cite-as 	    = The target of the link is a persistent URI for the resource that is the origin of the link. When accessing the persistent URI, it redirects to that origin resource.
describedby 	= The target of the link provides metadata that describes the resource that is the origin of the link. It is the inverse of the describes relation type.
describes 	    = The origin of the link is a resource that provides metadata that describes the resource that is the target of the link. It is the inverse of the describedby relation type.
type 	        = The target of the link is the URI for a class of resources to which the resource that is the origin of the link belongs.
license 	    = The target of the link is the URI of a license that applies to the resource that is the origin of the link.
item 	        = The origin of the link is a collection of resources and the target of the link is a resource that belongs to that collection. It is the inverse of the collection relation type.
collection 	    = The origin of the link is a resource that belongs to a collection and the target of the link is the collection to which it belongs. It is the inverse of the item relation type.

item <-> collection
describedby <-> describes
"""  # noqa: E501

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING, Any, Literal, cast, overload
from urllib.parse import urljoin

if TYPE_CHECKING:
    from invenio_records_resources.services.records.results import RecordItem
from signposting import AbsoluteURI, LinkRel, Signpost

from oarepo_runtime.proxies import current_runtime
from oarepo_runtime.typing import record_from_result


def signpost_link_to_str(signpost_link: Signpost) -> str:
    """Convert a signpost link to string."""
    link_str = str(signpost_link)
    if link_str[:6] == "Link: ":
        return f"{link_str[6:]}"
    raise ValueError(f"Invalid signpost link: {link_str}")  # pragma: no cover


def signpost_link_to_dict(link: Signpost) -> dict[str, Any]:
    """Convert signpost link to a dictionary."""
    link_dict: dict[str, Any] = {"href": link.target}
    if link.type:
        link_dict["type"] = link.type
    return link_dict


def signpost_link_to_additional_link(
    link: Signpost, landing_page_url: str, as_dict: bool = True
) -> Signpost | dict[str, Any] | None:
    """Transform signpost link to additional link with inversed relation type..

    Args:
        link: A signpost link to transform
        landing_page_url: landing page url which will be passed to href
        as_dict: if true, return dict, else return Signpost

    Returns: Additional link as dict or Signpost or None if relation type does no thave additional link.

    """
    match link.rel:
        case LinkRel.item:
            if as_dict:
                return {
                    "anchor": link.target,
                    str(LinkRel.collection): [{"href": landing_page_url, "type": "text/html"}],
                }
            return Signpost(
                rel=LinkRel.collection, target=landing_page_url, media_type="text/html", context=link.target
            )
        case LinkRel.describedby:
            if as_dict:
                return {
                    "anchor": link.target,
                    str(LinkRel.describes): [{"href": landing_page_url, "type": "text/html"}],
                }
            return Signpost(rel=LinkRel.describes, target=landing_page_url, media_type="text/html", context=link.target)
        case LinkRel.cite_as:
            return None
        # anchor is generated only for item & describedby, not for license
        case _:
            return None


def anchor_signpost_link(signpost_link: Signpost, anchor_url: str) -> Signpost:
    """Add anchor to a signpost link."""
    signpost_link.context = AbsoluteURI(anchor_url)
    return signpost_link


@overload
def get_additional_links(
    list_of_signpost_links: list[Signpost], landing_page_url: str, as_dict: Literal[True] = True
) -> list[dict[str, Any]]: ...


@overload
def get_additional_links(
    list_of_signpost_links: list[Signpost], landing_page_url: str, as_dict: Literal[False]
) -> list[Signpost]: ...


def get_additional_links(
    list_of_signpost_links: list[Signpost], landing_page_url: str, as_dict: bool = True
) -> list[Signpost] | list[dict[str, Any]]:
    """Create a list of additional links from a list of signpost links.

    Args:
        list_of_signpost_links: list of signpost link objects to be formatted
        landing_page_url: landing page url
        as_dict: if true, return a list of signpost link dicts, else return a list of Signpost link objects
    Returns: list of signpost link dicts or list of Signpost link objects

    """
    results = [
        result
        for signpost_link in list_of_signpost_links
        if (
            result := signpost_link_to_additional_link(
                link=signpost_link, landing_page_url=landing_page_url, as_dict=as_dict
            )
        )
        is not None
    ]
    if as_dict:
        return cast("list[dict[str, Any]]", results)
    return cast("list[Signpost]", results)


def list_of_signpost_links_to_http_header(links_list: list[Signpost]) -> str:
    """Create an HTTP Link header from a list of signpost links.

    Args:
        links_list: list of signpost link objects to be formatted

    Returns: signpost header with formatted links.

    """
    links = [str(link)[6:] for link in links_list if str(link)[:6] == "Link: "]
    return f"Link: {', '.join(links)}"


def create_linkset(datacite_dict: dict, record_item: RecordItem) -> str:
    """Create a linkset for the record item in the application/linkset format.

    Args:
        datacite_dict:  dictionary with datacite data
        record_item: record item, for which signpost links should be generated

    Returns: linkset in string format

    """
    landing_page_url = record_item.links.get("self_html")
    # just sanity check, we don't expect this to happen, not covered in tests
    if not landing_page_url:  # pragma: no cover
        return ""
    landing_page_links = landing_page_signpost_links_list(datacite_dict, record_item, short=False)
    additional_links: list[Signpost] = get_additional_links(landing_page_links, landing_page_url, as_dict=False)
    anchored_links = [
        anchor_signpost_link(signpost_link, landing_page_url) for signpost_link in landing_page_links
    ] + additional_links
    links = [str(link)[6:] for link in anchored_links if str(link)[:6] == "Link: "]
    return ", ".join(links)


def create_linkset_json(datacite_dict: dict, record_item: RecordItem) -> dict[str, list[dict[str, Any]]]:
    """Create a linkset for the record item in the application/linkset+json format.

    Args:
        datacite_dict:  dictionary with datacite data
        record_item: record item, for which signpost links should be generated

    Returns: linkset in JSON format

    """
    landing_page_url = record_item.links.get("self_html")
    # just sanity check, we don't expect this to happen, not covered in tests
    if not landing_page_url:  # pragma: no cover
        return {}
    landing_page_links = landing_page_signpost_links_list(datacite_dict, record_item, short=False)
    dict_of_links_by_relation = defaultdict(list)
    for link in landing_page_links:
        dict_of_links_by_relation[str(link.rel)].append(link)
    links_json = defaultdict(list)
    links_json["anchor"] = landing_page_url

    additional_links: list[dict[str, Any]] = get_additional_links(landing_page_links, landing_page_url)
    for link_relation_from_dict, list_of_links_for_relation in dict_of_links_by_relation.items():
        for link in list_of_links_for_relation:
            links_json[link_relation_from_dict].append(signpost_link_to_dict(link))

    return {"linkset": [dict(links_json), *[x for x in additional_links if x]]}


def file_content_signpost_links_list(record_item: RecordItem) -> list[Signpost]:
    """Create a list of signpost links for the file content of the record item.

    Args:
        record_item: record item with the file to generate a signpost link for

    Returns: list with the signpost link for the file content

    """
    record = record_from_result(record_item)
    model = current_runtime.get_model_for_record(record)
    landing_page_url = model.ui_url(view_name="record_detail", pid_value=record.pid.pid_value)
    if not landing_page_url:  # pragma: no cover
        return []
    return [
        Signpost(
            rel=LinkRel.linkset,
            target=landing_page_url,
            media_type="application/linkset",
        ),
        Signpost(
            rel=LinkRel.linkset,
            target=landing_page_url,
            media_type="application/linkset+json",
        ),
        Signpost(
            rel=LinkRel.collection,
            target=landing_page_url,
            media_type="text/html",
        ),
    ]


def export_format_signpost_links_list(record_item: RecordItem) -> list[Signpost]:
    """Create a list of signpost links for the export format of the record item.

    Args:
    record_item: record item with the export format to generate a signpost link for
    code: code of the export format

    Returns: list with the signpost link for the export format

    """
    return [
        Signpost(
            rel=LinkRel.linkset,
            target=record_item.links["self_html"],
            media_type="application/linkset",
        ),
        Signpost(
            rel=LinkRel.linkset,
            target=record_item.links["self_html"],
            media_type="application/linkset+json",
        ),
        Signpost(rel=LinkRel.describes, target=record_item.links["self_html"], media_type="text/html"),
    ]


def landing_page_signpost_links_list(datacite_dict: dict, record_item: RecordItem, short: bool) -> list[Signpost]:
    """Create a list of signpost links for the landing page of the record item.

    Args:
        datacite_dict: dictionary with datacite data
        record_item: record item, for which signpost links should be generated
        short: If true, lists only the first three links for relations with greater count

    Returns: list of signpost links for the landing page

    """
    signposting_links: list[Signpost] = []
    record = record_from_result(record_item)
    record_data = record_item.data  # self.html
    record_files = record_data.get("files", {}).get("entries", {})
    model = current_runtime.get_model_for_record(record)

    # author - prvni tri
    data = datacite_dict["data"]
    attributes = data["attributes"]
    creators = attributes.get("creators", [])
    if short:
        creators = creators[:3]
    for attribute in creators:
        signposting_links.extend(
            Signpost(rel=LinkRel.author, target=name_identifier["nameIdentifier"])
            for name_identifier in attribute["nameIdentifiers"]
        )

    # cite-as = DOI
    signposting_links.append(Signpost(rel=LinkRel.cite_as, target=urljoin("https://doi.org/", attributes.get("doi"))))

    # describedby
    for model_export in model.exports:
        model_export_url = model.ui_url(
            view_name="export", pid_value=record.pid.pid_value, export_format=model_export.code
        )
        # just sanity check, we don't expect this to happen, not covered in tests
        if not model_export_url:  # pragma: no cover
            continue
        signposting_links.append(
            Signpost(rel=LinkRel.describedby, target=model_export_url, media_type=model_export.mimetype)
        )

    # item
    record_file_values = record_files.values()
    if short:
        record_file_values = list(record_file_values)[:3]
    record_files_url = record_item.links.get("files")
    if record_files_url:
        signposting_links.extend(
            Signpost(
                rel=LinkRel.item,
                media_type=record_file.get("mimetype"),
                target=f"{record_files_url}/{record_file.get('key')}",
            )
            for record_file in record_file_values
        )

    # license
    for attribute in attributes.get("rightsList"):
        # check for schemeUri, rightsIdentifier and 'rightsIdentifierScheme' == SPDX, fallback rightsUri, else nothing
        license_url = attribute.get("rightsUri")
        if (
            attribute.get("schemeUri")
            and attribute.get("rightsIdentifier")
            and attribute.get("rightsIdentifierScheme") == "SPDX"
        ):
            license_url = urljoin(attribute.get("schemeUri"), attribute.get("rightsIdentifier"))
        signposting_links.append(Signpost(rel=LinkRel.license, target=license_url))

    # type
    schema_org = attributes.get("types", {}).get("schemaOrg")
    if schema_org:
        resource_type_url = "https://schema.org/" + schema_org
        signposting_links.append(Signpost(rel=LinkRel.type, target=resource_type_url))
    signposting_links.append(Signpost(rel=LinkRel.type, target="https://schema.org/AboutPage"))

    return signposting_links


def record_to_linkset(record_item: RecordItem) -> str:
    """Create a linkset from the record item. Get datacite to build linkset from model exports."""
    record = record_from_result(record_item)
    model = current_runtime.get_model_for_record(record)
    datacite_export = model.get_export_by_mimetype("application/vnd.datacite.datacite+json")
    if not datacite_export:
        return ""
    datacite_dict = datacite_export.serializer.serialize_object(record)
    return create_linkset(datacite_dict, record_item)


def record_to_json_linkset(record_item: RecordItem) -> dict[str, list[dict[str, Any]]]:
    """Create a JSON linkset from the record item. Get datacite to build linkset from model exports."""
    record = record_from_result(record_item)
    model = current_runtime.get_model_for_record(record)
    datacite_export = model.get_export_by_mimetype("application/vnd.datacite.datacite+json")
    if not datacite_export:
        return {}
    datacite_dict = datacite_export.serializer.serialize_object(record)
    return create_linkset_json(datacite_dict, record_item)
