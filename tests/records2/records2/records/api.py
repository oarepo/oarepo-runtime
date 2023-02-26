from invenio_pidstore.providers.recordid_v2 import RecordIdProviderV2
from invenio_records.systemfields import ConstantField
from invenio_records_resources.records.api import Record
from invenio_records_resources.records.systemfields import IndexField
from invenio_records_resources.records.systemfields.pid import PIDField, PIDFieldContext

from records2.records.dumper import Records2Dumper
from records2.records.models import Records2Metadata


class Records2Record(Record):
    model_cls = Records2Metadata

    schema = ConstantField("$schema", "local://records2-1.0.0.json")

    index = IndexField("records2-records2-1.0.0")

    pid = PIDField(
        create=True, provider=RecordIdProviderV2, context_cls=PIDFieldContext
    )

    dumper_extensions = []
    dumper = Records2Dumper(extensions=dumper_extensions)
