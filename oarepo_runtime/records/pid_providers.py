from invenio_pidstore.models import PersistentIdentifier, PIDStatus


class UniversalPIDMixin:
    unpid_pid_type = "unpid"
    unpid_default_status = PIDStatus.REGISTERED

    @classmethod
    def create(cls, object_type=None, object_uuid=None, options=None, **kwargs):
        pid = super().create(
            object_type=object_type, object_uuid=object_uuid, options=options, **kwargs
        )
        assert pid.pid.pid_value is not None
        control_pid = PersistentIdentifier.create(
            cls.unpid_pid_type,
            pid.pid.pid_value,
            pid_provider=None,
            object_type=object_type,
            object_uuid=object_uuid,
            status=cls.unpid_default_status,
        )
        return pid