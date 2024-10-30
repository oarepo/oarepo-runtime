import json, random
from flask import Response, Blueprint
from flask import current_app as flask_current_app
from invenio_db import db # sql alchemy session
from invenio_cache import current_cache # redis
import redis
from invenio_search import current_search_client # opensearch
from celery import current_app as celery_current_app, shared_task


def check_db_connection():
    if not has_database_connection():
        return "DB connection failed"
    else:
        return "ok"

def has_database_connection():
    try:
        db.session.execute("select * from alembic_version").scalar()
        return True
    except:
        return False
    finally:
        db.session.rollback()

def check_cache_connection():
    try:
        rand = random.randint(1, 1000)
        if current_cache.set('mykey', str(rand)):
            val = current_cache.get('mykey')
            if val == str(rand):
                return "ok"
            else:
                return "Cache returned unexpected value."
        else:
            return "Failed to set cache key."
    except redis.exceptions.ConnectionError as e:
        if isinstance(e.__cause__, ConnectionRefusedError):
            return "Cache connection error"
        return "Cache exception"
    except Exception as other:
        return str(other)



#  https://github.com/celery/celery/issues/4283
def check_message_queue():
    from kombu.exceptions import OperationalError
    try:
        #celery_current_app.autodiscover_tasks(['oarepo_runtime.info'])
        ping_task = celery_current_app.send_task('ping')
        if ping_task.get(timeout=2) == 'pong':
            return "ok"
    except OperationalError as e:
        if isinstance(e.__cause__, ConnectionRefusedError):
            return "RabbitMQ connection refused"
        return "Other RabbitMQ-related error"
    except Exception as other:
        return str(other)


def check_opensearch():
    try:
        is_available = current_search_client.ping()
        if is_available:
            return "ok"
        else:
            return "OpenSearch is not available"
    except Exception as e:
        return str(e)


blueprint = Blueprint("repository-check", __name__, url_prefix="/.well-known")

@blueprint.route("/check")
def check_connections() -> Response:
    """
    Function to check all necessary connections (database, redis, rabbitmq, opensearch)
    Return Response 200 if everything is OK or Response 500 with json and all failed tests
    """
    check_list = {}
    with flask_current_app.app_context():
        check_list['db'] = check_db_connection()
        check_list['cache'] = check_cache_connection()
        check_list['mq'] = check_message_queue()
        check_list['opensearch'] = check_opensearch()

    failed_checks = {key: value for key, value in check_list.items() if value != 'ok'}

    if failed_checks:
        return Response(json.dumps(failed_checks), status=500, content_type='application/json')

    return Response(json.dumps(check_list), status=200, content_type='application/json') # good


