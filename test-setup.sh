#!/usr/bin/env bash
#
# This script sets up the testing environment by installing
# the mock module from the tests directory.
#
source .venv/bin/activate

echo "Installing mock-module to the current environment"
uv pip install tests/mock-module