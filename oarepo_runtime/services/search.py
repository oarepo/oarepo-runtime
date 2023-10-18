from invenio_records_resources.services.records import SearchOptions as InvenioSearchOptions

# TODO: integrate this to invenio_records_resources.services.records
from flask_babelex import lazy_gettext as _


class SearchOptions(InvenioSearchOptions):
    sort_options = {
        "bestmatch": dict(
            title=_("Best match"),
            fields=["_score"],  # ES defaults to desc on `_score` field
        ),
        "newest": dict(
            title=_("Newest"),
            fields=["-created"],
        ),
        "oldest": dict(
            title=_("Oldest"),
            fields=["created"],
        ),
    }
