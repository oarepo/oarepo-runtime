#!/bin/bash

set -e
pip install -e '.[tests]'

MODEL="records2"
VENV=".model_venv"

if test -d ./tests/$MODEL; then
	rm -rf ./tests/$MODEL
fi

if test -d ./$VENV; then
	rm -rf ./$VENV
fi

oarepo-compile-model ./tests/$MODEL.yaml --output-directory ./tests/$MODEL -vvv
python3 -m venv $VENV
. $VENV/bin/activate
pip install -U setuptools pip wheel
pip install "./tests/$MODEL[tests]"
rm -rf ./tests/$MODEL/tests
pytest tests
