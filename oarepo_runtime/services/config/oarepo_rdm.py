from invenio_rdm_records.services.components import DefaultRecordsComponents
from invenio_rdm_records.services.config import RDMRecordServiceConfig

OarepoRDMComponents = [
    *DefaultRecordsComponents
]

class OarepoRDMServiceConfig(RDMRecordServiceConfig):
    
    components = OarepoRDMComponents