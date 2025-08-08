#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Extension preset for runtime module."""

from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Any

from flask import current_app
from invenio_records_resources.proxies import current_service_registry

if TYPE_CHECKING:
    from flask import Flask


class OARepoRuntime:
    """OARepo base of invenio oarepo client."""

    def __init__(self, app: Flask | None = None):
        """Extension initialization."""
        if app:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Flask application initialization."""
        self.app = app
        app.extensions["oarepo-runtime"] = self

    def get_record_service_for_record(self, record: Any) -> Any:
        """Retrieve the associated service for a given record."""
        if not record:
            return None
        return self.get_record_service_for_record_class(type(record))

    def get_record_service_for_record_class(self, record_cls: Any) -> Any:
        """Retrieve the service associated with a given record class."""
        warnings.warn(
            "The implementation for `get_record_service_for_record` "
            "needs to be changed to use different configuration.",
            stacklevel=2,
        )

        service_id = current_app.config["OAREPO_PRIMARY_RECORD_SERVICE"][record_cls]
        return current_service_registry.get(service_id)
