from invenio_rdm_records.services.components import DefaultRecordsComponents
from invenio_rdm_records.services.config import RDMRecordServiceConfig

OarepoRDMComponents = [
    *DefaultRecordsComponents
]

class OarepoRDMServiceConfig(RDMRecordServiceConfig):
    """If service config is inherited directly from the RDM service config, model builder will generate components incorrectly"""

    components = OarepoRDMComponents