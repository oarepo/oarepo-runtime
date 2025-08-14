#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Extensions for RDM API resources."""

from __future__ import annotations

from typing import TYPE_CHECKING

from flask_resources.responses import ResponseHandler
from invenio_records_resources.resources.records.headers import etag_headers

if TYPE_CHECKING:
    from collections.abc import Iterable

    from oarepo_runtime.api import Export


def exports_to_response_handlers(
    exports: Iterable[Export],
) -> dict[str, ResponseHandler]:
    """Convert exports to a dictionary of mimetype -> response handlers."""
    return {
        export.mimetype: ResponseHandler(
            serializer=export.serializer,
            headers=etag_headers,
        )
        for export in exports
    }
