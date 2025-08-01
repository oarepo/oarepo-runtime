from flask import current_app
from flask_principal import Identity, UserNeed, identity_loaded
from invenio_access.models import User


def get_user_and_identity(user_id=None, username=None, email=None):
    def lookup_user():
        if user_id is not None:
            return User.query.filter_by(id=user_id).one()
        elif username is not None:
            return User.query.filter_by(username=username).one()
        elif email is not None:
            return User.query.filter_by(email=email).one()
        else:
            raise ValueError(
                "At least one of user_id, username, or email must be provided."
            )

    user = lookup_user()

    identity = Identity(user.id)
    identity.provides.add(UserNeed(user.id))
    if (
        hasattr(current_app.wsgi_app, "mounts")
        and "/api" in current_app.wsgi_app.mounts
    ):
        # called from UI
        api_app = current_app.wsgi_app.mounts["/api"]
    else:
        # called from API
        api_app = current_app
    with api_app.app_context():
        with current_app.test_request_context("/api"):
            identity_loaded.send(api_app, identity=identity)
    return user, identity
