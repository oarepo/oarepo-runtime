"""Update mappings for all record classes in the service registry."""

from __future__ import annotations

from typing import TYPE_CHECKING

from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.services.records import (
    RecordService,
    RecordServiceConfig,
)

from oarepo_runtime.records.mapping import update_record_system_fields_mapping

if TYPE_CHECKING:
    from invenio_records_resources.services.base import Service


def update_all_record_mappings() -> None:
    """Update all mappings for the registered record classes."""
    service: Service
    for (
        service
    ) in current_service_registry._services.values():  # type: ignore[attr-defined]  # noqa: SLF001
        if not isinstance(service, RecordService):
            continue

        config: RecordServiceConfig = service.config

        record_class = getattr(config, "record_cls", None)
        if record_class:
            update_record_system_fields_mapping(record_class)

        draft_class = getattr(config, "draft_cls", None)
        if draft_class:
            update_record_system_fields_mapping(draft_class)
