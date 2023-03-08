#!/bin/bash

set -e 

pip install -e '.[tests]'
pip install -e 'tests/records2'
pip list
export PYTHONPATH=.

pytest tests
