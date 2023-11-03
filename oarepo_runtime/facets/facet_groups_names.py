from typing import List

from flask_principal import Identity
from invenio_records_resources.services import SearchOptions as InvenioSearchOptions


def facet_groups_names(
    identity: Identity, search_options: InvenioSearchOptions, params
) -> List[str]:
    """
    Default implementation for Flask-principal identity.
    """

    if hasattr(identity, "provides"):
        return [need.value for need in identity.provides if need.method == "role"]

    return []
