from invenio_search import current_search_client
from invenio_search.engine import dsl
from invenio_search.utils import build_alias_name


def prefixed_index(index):
    return dsl.Index(
        build_alias_name(
            index._name,
        ),
        using=current_search_client,
    )
