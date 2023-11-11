from invenio_records.dictutils import dict_set
from invenio_records.systemfields import SystemField
from sqlalchemy.orm.exc import NoResultFound

from oarepo_runtime.services.custom_fields import CustomFieldsMixin


# taken from https://github.com/inveniosoftware/invenio-rdm-records/blob/master/invenio_rdm_records/records/systemfields/has_draftcheck.py
class HasDraftCheckField(CustomFieldsMixin, SystemField):
    """PID status field which checks against an expected status."""

    def __init__(self, draft_cls=None, key=None, **kwargs):
        """Initialize the PIDField.

        It stores the `record.has_draft` value in the secondary storage
        system's record or defaults to `False` if the `draft_cls` is not passed
        e.g Draft records.

        :param key: Attribute name of the HasDraftCheckField.
        :param draft_cls: The draft class to use for querying.
        """
        super().__init__(key=key, **kwargs)
        self.draft_cls = draft_cls

    #
    # Data descriptor methods (i.e. attribute access)
    #
    def __get__(self, record, owner=None):
        if record is None:
            return self  # returns the field itself.

        # If not draft_cls is passed return False
        if self.draft_cls is None:
            return False

        try:
            self.draft_cls.get_record(record.id)
            return True
        except NoResultFound:
            return False

    def pre_dump(self, record, data, **kwargs):
        dict_set(data, self.key, record.has_draft)
