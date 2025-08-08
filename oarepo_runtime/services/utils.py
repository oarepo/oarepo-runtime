#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-model (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Module to retrieve services associated with records and record classes."""

from __future__ import annotations

from typing import Any

from flask import current_app
from invenio_records_resources.proxies import current_service_registry


def get_record_service_for_record(record: Any) -> Any:
    """Retrieve the associated service for a given record."""
    if not record:
        return None
    return get_record_service_for_record_class(type(record))


def get_record_service_for_record_class(record_cls: Any) -> Any:
    """Retrieve the service associated with a given record class."""
    service_id = current_app.config["OAREPO_PRIMARY_RECORD_SERVICE"][record_cls]
    return current_service_registry.get(service_id)
