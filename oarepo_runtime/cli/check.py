import json
import random
import traceback

import click
import kombu.exceptions
import opensearchpy
import redis
from flask import current_app
from flask.cli import with_appcontext
from invenio_db import db
from invenio_files_rest.models import Location
from invenio_pidstore.models import PersistentIdentifier
from invenio_records_resources.proxies import current_service_registry
from opensearchpy import TransportError

from .base import oarepo


@oarepo.command(name="check")
@click.argument("output_file", default="-")
@with_appcontext
def check(output_file):
    status = {}
    status["db"] = check_database()
    status["opensearch"] = check_opensearch()
    status["files"] = check_files()
    status["mq"] = check_message_queue()
    status["cache"] = check_cache()
    if output_file == "-":
        print(
            json.dumps(status, indent=4, ensure_ascii=False, default=lambda x: str(x))
        )
    else:
        with open(output_file, "w") as f:
            json.dump(status, f, ensure_ascii=False, default=lambda x: str(x))


def check_database():
    if not has_database_connection():
        return "connection_error"
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
                return "connection_error"


        try:
            index = indexer._prepare_index(indexer.record_to_index(record_class))
        except AttributeError:
            print(f"Warning: can not get index name for record class {record_class}")
            continue

        try:
            service.indexer.client.indices.get(index=index)
        except TransportError:
            return f"index_missing:{index}"
    return "ok"


def check_files():
    if not has_database_connection():
        return "db_connection_error"

    try:
        db.session.begin()
        # check that there is the default location and that is readable
        default_location = Location.get_default()
        if not default_location:
            return "default_location_missing"
    except:  # NOSONAR - we are not interested what the exception is
        return "db_error"
    finally:
        db.session.rollback()

    try:
        import s3fs
    except ImportError:
        return f"s3_support_not_installed"

    try:
        info = current_app.extensions["invenio-s3"].init_s3fs_info
        fs = s3fs.S3FileSystem(default_block_size=4096, **info)
        fs.ls(default_location.uri.replace("s3://", ""))
    except:  # NOSONAR - we are not interested what the exception is
        return f"bucket_does_not_exist:{default_location.uri}"

    return "ok"


def check_message_queue():
    try:
        from celery import current_app

        current_app.control.inspect().active()
        return "ok"
    except kombu.exceptions.OperationalError as e:
        if isinstance(e.__cause__, ConnectionRefusedError):
            return "connection_error"
        return "mq_error"
    except:  # NOSONAR - we are not interested what the exception is
        return "mq_error"


def check_cache():
    try:
        from invenio_cache.proxies import current_cache

        rnd = str(
            random.randint(0, 10000)  # NOSONAR - this is not a cryptographic random
        )
        # it is here just to make sure that what we put to the cache is what we get back

        current_cache.set("oarepo_check", rnd)
        if current_cache.get("oarepo_check") == rnd:
            return "ok"
        else:
            return "cache_error"
    except redis.exceptions.ConnectionError as e:
        if isinstance(e.__cause__, ConnectionRefusedError):
            return "connection_error"
        return "cache_exception"
    except:  # NOSONAR - we are not interested what the exception is
        traceback.print_exc()
        return "cache_exception"
