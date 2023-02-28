#!/bin/bash

set -e 

pip install -e '.[tests]'
pip install -e 'tests/records2'
export PYTHONPATH=.

pytest tests
