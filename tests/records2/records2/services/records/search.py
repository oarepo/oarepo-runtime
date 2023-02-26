from invenio_records_resources.services import SearchOptions as InvenioSearchOptions

from . import facets


def _(x):
    """Identity function for string extraction."""
    return x


class Records2SearchOptions(InvenioSearchOptions):
    """Records2Record search options."""

    facets = {
        "metadata_title": facets.metadata_title,
        "_id": facets._id,
        "created": facets.created,
        "updated": facets.updated,
        "_schema": facets._schema,
    }
    sort_options = {
        **InvenioSearchOptions.sort_options,
    }
