from flask import current_app

from records2.services.records.config import Records2ServiceConfig


def test_permissions_with_config_key(app, db, non_system_identity, search_clear, location):
    """
    Changing the preset of the model to be read_only
    and checking that the identity is not allowed
    to create a record.
    """
    # just to check that the cache invalidation below works
    print(Records2ServiceConfig.permission_policy_cls)
    try:
        current_app.config['RECORDS2_SERVICE_PERMISSIONS_PRESETS'] = [
            "read_only"
        ]

        permission_class = Records2ServiceConfig().permission_policy_cls
        permission_policy = permission_class("create")
        assert not permission_policy.allows(non_system_identity)
    finally:
        del current_app.config['RECORDS2_SERVICE_PERMISSIONS_PRESETS']

def test_permissions_without_config_key(app, db, non_system_identity, search_clear, location):
    """
    Default setting is everyone, so the identity should be able to create a record
    """

    permission_class = Records2ServiceConfig().permission_policy_cls
    permission_policy = permission_class("create")
    assert permission_policy.allows(non_system_identity)