# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o
# SPDX-License-Identifier: MIT

"""Safe XML parsing and element-level (de)serializer protocols.

Serializers and deserializers that work with XML can implement the element-level
protocols below in addition to the string-based flask-resources API. Callers that
already have (or want) an lxml element, such as the OAI-PMH harvester and server or
``ExportRepresentation.XML`` exports, can then skip a serialize/parse round trip.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, runtime_checkable

from lxml import etree
from marshmallow import ValidationError

if TYPE_CHECKING:
    from lxml.etree import _Element

SAFE_XML_PARSER = etree.XMLParser(
    resolve_entities=False,
    load_dtd=False,
    no_network=True,
    huge_tree=False,
)
"""XML parser for untrusted input (API clients, remote OAI-PMH servers).

It does not expand entities, load DTDs or access the network, so it is not
vulnerable to XXE or entity expansion attacks.
"""


def parse_xml(data: str | bytes) -> _Element:
    """Parse untrusted XML with ``SAFE_XML_PARSER``.

    :raises marshmallow.ValidationError: if the data is not well-formed XML.
    """
    if isinstance(data, str):
        data = data.encode("utf-8")
    try:
        return etree.fromstring(data, SAFE_XML_PARSER)
    except etree.XMLSyntaxError as e:
        raise ValidationError([f"Invalid XML: {e}"]) from e


@runtime_checkable
class XMLDeserializer(Protocol):
    """Deserializer that can read an already parsed XML element."""

    def deserialize_xml(self, element: _Element) -> dict[str, Any]:
        """Deserialize the XML element into a record dictionary."""
        ...


@runtime_checkable
class XMLSerializer(Protocol):
    """Serializer that can produce an XML element instead of a string."""

    def serialize_object_xml(self, obj: Any) -> _Element:
        """Serialize the record dictionary into an XML element."""
        ...
