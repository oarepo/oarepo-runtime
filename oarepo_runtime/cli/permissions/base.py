from flask import current_app
from flask_principal import Identity, UserNeed, identity_loaded
from invenio_access.models import User

from ..base import oarepo


@oarepo.group()
def permissions():
    """Commands for checking and explaining permissions."""


def get_user_and_identity(user_id_or_email):
    try:
        user_id = int(user_id_or_email)
        user = User.query.filter_by(id=user_id).one()
    except ValueError:
        user = User.query.filter_by(email=user_id_or_email).one()

    identity = Identity(user.id)
    identity.provides.add(UserNeed(str(user.id)))
    api_app = current_app.wsgi_app.mounts["/api"]
    with api_app.app_context():
        with current_app.test_request_context("/api"):
            identity_loaded.send(api_app, identity=identity)
    return user, identity
