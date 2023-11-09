#!/bin/bash

set -e

OAREPO_VERSION="${OAREPO_VERSION:-11}"
OAREPO_VERSION_MAX=$((OAREPO_VERSION+1))

BUILDER_VENV=.venv-builder
if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi

python3 -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
pip install -U oarepo-model-builder oarepo-model-builder-files

if test -d records2 ; then
  rm -rf records2
fi

oarepo-compile-model ./tests/records2.yaml --output-directory records2 --profile record,files -vvv

VENV=".venv"

if test -d $VENV ; then
  rm -rf $VENV
fi

python3 -m venv $VENV
. $VENV/bin/activate
pip install -U setuptools pip wheel

pip install "oarepo>=${OAREPO_VERSION},<${OAREPO_VERSION_MAX}"
pip install -e ".[tests,oarepo-${OAREPO_VERSION:-11}]"
pip install -e records2
# pip install -e records

pip uninstall -y uritemplate
pip install uritemplate

invenio index destroy --force --yes-i-know || true

## run OOM separately as it needs its own configuration of logging
pytest -m "not oom" tests
pytest -m "oom" tests


test -d $VENV/var/instance || mkdir $VENV/var/instance
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
cat tests/records2_async_data/invenio.cfg | sed "s/POSTGRES_HOST/${POSTGRES_HOST}/g" > $VENV/var/instance/invenio.cfg

invenio db destroy --yes-i-know || true
invenio db init create
invenio index destroy --force --yes-i-know || true
invenio index init
invenio oarepo cf init
invenio files location create --default default file:////tmp/data



celery -A invenio_app.celery worker -l INFO -c 1 &
CELERY_PID=$!

trap "kill $CELERY_PID" EXIT

sleep 5

python tests/records2_async_data/generate_async_data_for_import.py /tmp/sample-records-for-import 100
invenio oarepo fixtures load --no-system-fixtures /tmp/sample-records-for-import --on-background --bulk-size 10
python tests/records2_async_data/check_async_data_loaded.py 100