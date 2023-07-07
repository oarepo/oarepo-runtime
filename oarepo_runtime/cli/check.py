import json

import click
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_resources.proxies import current_service_registry
from opensearchpy import TransportError

from .base import oarepo


@oarepo.command(name="check")
@click.argument("output_file")
@with_appcontext
def check(output_file):
    status = {}
    status["db"] = check_database()
    status["opensearch"] = check_opensearch()
    status["files"] = check_files()
    if output_file == "-":
        print(json.dumps(status, indent=4, ensure_ascii=False))
    else:
        with open(output_file, "w") as f:
            json.dump(status, f)


def check_database():
    try:
        db.session.begin()
        try:
            PersistentIdentifier.query.all()[:1]
        except:
            return "not_initialized"
        alembic = current_app.extensions["invenio-db"].alembic
        context = alembic.migration_context
        db_heads = set(context.get_current_heads())
        source_heads = [x.revision for x in alembic.current()]
        for h in source_heads:
            if h not in db_heads:
                return "migration_pending"
        return "ok"
    finally:
        db.session.rollback()


def check_opensearch():
    services = current_service_registry._services.keys()
    for service_id in services:
        service = current_service_registry.get(service_id)
        record_class = getattr(service.config, "record_cls", None)
        if not record_class:  # files??
            continue

        indexer = getattr(service, "indexer", None)
        if not indexer:
            continue
        index = indexer._prepare_index(indexer.record_to_index(record_class))
        try:
            service.indexer.client.indices.get(index=index)
        except TransportError:
            return f"index-missing:{index}"
    return "ok"


def check_files():
    try:
        db.session.begin()
        # check that there is the default location and that is readable
        default_location = Location.get_default()
        if default_location:
            return "ok"
        else:
            return "default-location-missing"
    except:
        return "db-error"
    finally:
        db.session.rollback()
