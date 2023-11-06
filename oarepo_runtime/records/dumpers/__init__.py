from invenio_records.dumpers import SearchDumper as InvenioSearchDumper


class SearchDumper(InvenioSearchDumper):
    extensions = []

    def __init__(self, **kwargs):
        super().__init__(extensions=self.extensions, **kwargs)
