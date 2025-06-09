from flask_babel import get_locale
from invenio_records_resources.services.records.facets import TermsFacet

class MultilingualFacet(TermsFacet):

    def __init__(self, lang_facets, **kwargs):

        self.lang_facets = lang_facets

        super().__init__(**kwargs)

    def get_aggregation(self):
        return self.lang_facets[get_locale().language].get_aggregation()

    def get_value(self, bucket):
        """Get key value for a bucket."""
        return self.lang_facets[get_locale().language].get_value(bucket)

    def get_label_mapping(self, buckets):
        """Overwrite this method to provide custom labelling."""
        return self.lang_facets[get_locale().language].get_label_mapping(buckets)

    def get_values(self, data, filter_values):
        """Get an unlabelled version of the bucket."""
        return self.lang_facets[get_locale().language].get_values(data, filter_values)

    def get_labelled_values(self, data, filter_values):
        """Get a labelled version of a bucket."""
        return self.lang_facets[get_locale().language].get_labelled_values(data, filter_values)

    def add_filter(self, filter_values):
        """Create a terms filter instead of bool containing term filters."""
        return self.lang_facets[get_locale().language].add_filter(filter_values)
