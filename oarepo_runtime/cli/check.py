import json
import random
import sys
import traceback

import click
import kombu.exceptions
import opensearchpy
import redis
import s3fs
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_resources.proxies import current_service_registry
from opensearchpy import TransportError
from werkzeug.local import LocalProxy

from .base import oarepo


@oarepo.command(name="check")
@click.argument("output_file")
@with_appcontext
def check(output_file):
    status = {}
    status["db"] = check_database()
    status["opensearch"] = check_opensearch()
    status["files"] = check_files()
    status["mq"] = check_message_queue()
    status["cache"] = check_cache()
    status["configuration"] = {
        k: v for k, v in current_app.config.items() if not isinstance(v, LocalProxy)
    }
    if output_file == "-":
        print(
            json.dumps(status, indent=4, ensure_ascii=False, default=lambda x: str(x))
        )
    else:
        with open(output_file, "w") as f:
            json.dump(status, f, ensure_ascii=False, default=lambda x: str(x))


def check_database():
    if not has_database_connection():
        return "connection-error"
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


def has_database_connection():
    try:
        db.session.begin()
        db.session.execute("SELECT 1")
        return True
    except:
        return False
    finally:
        db.session.rollback()


def check_opensearch():
    services = current_service_registry._services.keys()
    checked_indexers = set()
    for service_id in services:
        service = current_service_registry.get(service_id)
        record_class = getattr(service.config, "record_cls", None)
        if not record_class:  # files??
            continue
        indexer = getattr(service, "indexer", None)
        if not indexer:
            continue
        if id(indexer) not in checked_indexers:
            checked_indexers.add(id(indexer))
            try:
                indexer.client.indices.exists("test")
            except opensearchpy.exceptions.ConnectionError:
                return "connection-error"

        index = indexer._prepare_index(indexer.record_to_index(record_class))
        try:
            service.indexer.client.indices.get(index=index)
        except TransportError:
            return f"index-missing:{index}"
    return "ok"


def check_files():
    if not has_database_connection():
        return "db-connection-error"

    try:
        db.session.begin()
        # check that there is the default location and that is readable
        default_location = Location.get_default()
        if not default_location:
            return "default-location-missing"

        try:
            info = current_app.extensions["invenio-s3"].init_s3fs_info
            fs = s3fs.S3FileSystem(default_block_size=4096, **info)
            fs.ls(default_location.uri.replace("s3://", ""))
        except:
            return f"bucket-does-not-exist:{default_location.uri}"

        return "ok"
    except:
        return "db-error"
    finally:
        db.session.rollback()


def check_message_queue():
    try:
        from celery import current_app

        current_app.control.inspect().active()
        return "ok"
    except kombu.exceptions.OperationalError as e:
        if isinstance(e.__cause__, ConnectionRefusedError):
            return "connection-error"
        return "mq-error"
    except:
        return "mq-error"


def check_cache():
    try:
        from invenio_cache.proxies import current_cache

        rnd = str(random.randint(0, 10000))

        current_cache.set("oarepo_check", rnd)
        if current_cache.get("oarepo_check") == rnd:
            return "ok"
        else:
            return "cache-error"
    except redis.exceptions.ConnectionError as e:
        if isinstance(e.__cause__, ConnectionRefusedError):
            return "connection-error"
        return "cache-exception"
    except:
        traceback.print_exc()
        return "cache-exception"
