import time

from thesis.proxies import current_service
from invenio_access.permissions import system_identity

from thesis.records.api import ThesisDraft, ThesisRecord

"""
import logging
logging.basicConfig()
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
"""



def test_without_owners(db, app, identity, user, more_users, more_identities, search_clear, location):
    from invenio_pidstore.models import PersistentIdentifier
    print(f"before create {PersistentIdentifier.query.all()}")
    rec = current_service.create(identity, data={"metadata": {"title": "blah"}, "files": {"enabled": False}})
    print(f"after create {PersistentIdentifier.query.all()}")
    record_id = rec.data["id"]
    updated_rec1 = current_service.update_draft(more_identities[0], id_=record_id, data={"metadata": {"title": "blahblah"}, "files": {"enabled": False}})
    print(f"after update {PersistentIdentifier.query.all()}")
    updated_read = current_service.read_draft(identity, id_=record_id)
    """
    updated_rec2 = current_service.update_draft(more_identities[0], id_=record_id,
                                               data={"metadata": {"title": "blahblah"}})
    # publish
    ThesisDraft.index.refresh()
    publish_res = current_service.publish(system_identity, id_=record_id)
    ThesisDraft.index.refresh()
    ThesisRecord.index.refresh()
    published = current_service.read_draft(identity, id_=rec.data["id"])
    """

def test_owners(db, app, identity, user, more_users, more_identities, search_clear, location):
    rec = current_service.create(identity, data={"metadata": {"title": "blah"}})
    record_id = rec.data["id"]
    updated_rec1 = current_service.update_draft(more_identities[0], id_=record_id, data={"metadata": {"title": "blahblah"}})
    assert len(updated_rec1._obj.parent.owners) == 2
    updated_read = current_service.read_draft(identity, id_=record_id)
    assert len(updated_read._obj.parent.owners) == 2
    updated_rec2 = current_service.update_draft(more_identities[0], id_=record_id,
                                               data={"metadata": {"title": "blahblah"}})
    assert len(updated_rec2._obj.parent.owners) == 2
    # publish
    publish_res = current_service.publish(system_identity, id_=record_id)
    published = current_service.read(identity, id_=record_id)
    assert len(published._obj.parent.owners) == 2
    updated_rec = current_service.new_version(more_identities[1], id_=record_id)
    assert len(updated_rec._obj.parent.owners) == 2
    updated_rec = current_service.update_draft(more_identities[1], id_=updated_rec.data["id"],
                                         data={"metadata": {"title": "blahblah"}})
    assert len(updated_rec._obj.parent.owners) == 3

