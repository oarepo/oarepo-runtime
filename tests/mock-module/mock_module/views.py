# SPDX-FileCopyrightText: 2021 CERN
# SPDX-License-Identifier: MIT

"""Example views."""

from __future__ import annotations


def create_mock_blueprint(app):
    mock_module = app.extensions["mock-module"]
    return mock_module.resource.as_blueprint()
