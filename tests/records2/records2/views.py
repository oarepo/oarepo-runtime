from flask import Blueprint


def create_blueprint_from_app_records2(app):
    """Create  blueprint."""
    if app.config.get("RECORDS2_REGISTER_BLUEPRINT", True):
        blueprint = app.extensions["records2"].resource.as_blueprint()
    else:
        blueprint = Blueprint("records2", __name__, url_prefix="/empty/records2")
    blueprint.record_once(init_create_blueprint_from_app_records2)

    # calls record_once for all other functions starting with "init_addons_"
    # https://stackoverflow.com/questions/58785162/how-can-i-call-function-with-string-value-that-equals-to-function-name
    funcs = globals()
    funcs = [
        v
        for k, v in funcs.items()
        if k.startswith("init_addons_records2") and callable(v)
    ]
    for func in funcs:
        blueprint.record_once(func)

    return blueprint


def init_create_blueprint_from_app_records2(state):
    """Init app."""
    app = state.app
    ext = app.extensions["records2"]

    # register service
    sregistry = app.extensions["invenio-records-resources"].registry
    sregistry.register(ext.service, service_id="records2")

    # Register indexer
    if hasattr(ext.service, "indexer"):
        iregistry = app.extensions["invenio-indexer"].registry
        iregistry.register(ext.service.indexer, indexer_id="records2")
