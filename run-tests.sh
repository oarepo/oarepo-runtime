#!/bin/bash

PYTHON="${PYTHON:-python3}"

set -e

OAREPO_VERSION="${OAREPO_VERSION:-12}"
export PIP_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple
export UV_EXTRA_INDEX_URL=https://gitlab.cesnet.cz/api/v4/projects/1408/packages/pypi/simple

BUILDER_VENV=.venv-builder
if test -d $BUILDER_VENV ; then
	rm -rf $BUILDER_VENV
fi

$PYTHON -m venv $BUILDER_VENV
. $BUILDER_VENV/bin/activate
pip install -U setuptools pip wheel
pip install -U oarepo-model-builder oarepo-model-builder-files

if test -d records2 ; then
  rm -rf records2
fi

oarepo-compile-model ./tests/records2.yaml --output-directory records2 --profile record,files -vvv

pip install -U oarepo-model-builder-drafts oarepo-model-builder-drafts-files
if test -d thesis ; then
  rm -rf thesis
fi
oarepo-compile-model ./tests/thesis.yaml --output-directory thesis -vvv

VENV=".venv"

if test -d $VENV ; then
  rm -rf $VENV
fi

$PYTHON -m venv $VENV
. $VENV/bin/activate
pip install -U setuptools pip wheel nrp-devtools
nrp-devtools proxy 120 &

pip install "oarepo[tests, rdm]==${OAREPO_VERSION}.*"
pip install -e ".[tests]"
pip install -e records2
pip install pytest-invenio
pip install -e thesis

pip uninstall -y uritemplate
pip install uritemplate

invenio index destroy --force --yes-i-know || true

# run OOM separately as it needs its own configuration of logging
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

python3 tests/records2_async_data/generate_async_data_for_import.py /tmp/sample-records-for-import 100
invenio oarepo fixtures load --no-system-fixtures /tmp/sample-records-for-import --on-background --bulk-size 10
python3 tests/records2_async_data/check_async_data_loaded.py 100