#!/bin/bash
set -e

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

pip install -e '.[tests,oarepo-${OAREPO_VERSION:-11}]'
pip install -e records2
# pip install -e records

pip uninstall -y uritemplate
pip install uritemplate

pytest tests
