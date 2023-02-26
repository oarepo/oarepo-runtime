"""Facet definitions."""

from invenio_records_resources.services.records.facets import TermsFacet

metadata_title = TermsFacet(field="metadata.title")


_id = TermsFacet(field="id")


created = TermsFacet(field="created")


updated = TermsFacet(field="updated")


_schema = TermsFacet(field="$schema")
