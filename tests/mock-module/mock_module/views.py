#
# Copyright (C) 2021 CERN.
# Copyright (C) 2021 Northwestern University.
#
# Invenio-Drafts-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

# type: ignore  # noqa
"""Example views."""

from __future__ import annotations


def create_mock_blueprint(app):
    mock_module = app.extensions["mock-module"]
    return mock_module.resource.as_blueprint()
