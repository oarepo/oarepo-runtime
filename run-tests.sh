#!/bin/bash

set -e 

pip install -e '.[tests]'
pip install -e 'tests/records2'
pip uninstall -y uritemplate
pip install uritemplate
export PYTHONPATH=.

pytest tests
