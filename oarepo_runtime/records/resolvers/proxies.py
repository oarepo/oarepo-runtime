from invenio_pidstore.errors import PIDUnregistered
from invenio_records_resources.references.resolvers.records import RecordProxy
from sqlalchemy.exc import NoResultFound


class DraftProxy(RecordProxy):
    def _resolve(self):
        pid_value = self._parse_ref_dict_id()

        try:
            return self.record_cls.pid.resolve(pid_value, registered_only=False)
        except (PIDUnregistered, NoResultFound):
            # try checking if it is a published record before failing
            return self.record_cls.pid.resolve(pid_value)
