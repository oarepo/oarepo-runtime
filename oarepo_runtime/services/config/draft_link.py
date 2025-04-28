from invenio_records_resources.services import RecordLink

from oarepo_runtime.records.drafts import get_draft


class DraftLink(RecordLink):
    """Draft link."""

    def __init__(self, *args, **kwargs):
        """Initialize draft link."""
        super().__init__(*args, **kwargs)

    @staticmethod
    def vars(record, vars):
        """Variables for the URI template."""
        # Some records don't have record.pid.pid_value yet (e.g. drafts)
        RecordLink.vars(record, vars)
        draft_record = get_draft(record)

        if draft_record:
            pid_value = getattr(draft_record.pid, "pid_value", None)
            if pid_value:
                vars.update({"id": pid_value})
