from invenio_accounts.models import User
from invenio_drafts_resources.services.records.uow import ParentRecordCommitOp
from invenio_records_resources.services.records.components import ServiceComponent


class OwnersComponent(ServiceComponent):
    def create(self, identity, *, record, **kwargs):
        """Create handler."""
        owners = getattr(record.parent, "owners", None)
        if owners is not None:
            user = User.query.filter_by(id=identity.id).first()
            record.parent.owners.add(user)

    def update(self, identity, *, record, **kwargs):
        """Update handler."""
        owners = getattr(record.parent, "owners", None)
        if owners is not None:
            user = User.query.filter_by(id=identity.id).first()
            record.parent.owners.add(user)

    def update_draft(self, identity, *, record, **kwargs):
        """Update handler."""
        owners = getattr(record.parent, "owners", None)
        if owners is not None:
            user = User.query.filter_by(id=identity.id).first()
            record.parent.owners.add(user)
            self.uow.register(ParentRecordCommitOp(record.parent))
