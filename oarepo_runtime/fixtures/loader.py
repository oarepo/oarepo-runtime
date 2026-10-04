# SPDX-FileCopyrightText: 2026 CESNET z.s.p.o.
# SPDX-License-Identifier: MIT

"""Create or update a single record of a model from a fixture entry.

See :mod:`oarepo_runtime.fixtures` for the entry format.
"""

from __future__ import annotations

import hashlib
import logging
import threading
from contextlib import contextmanager
from contextvars import ContextVar
from functools import cache
from typing import TYPE_CHECKING, Any

import requests
from invenio_drafts_resources.services.records.service import RecordService as DraftRecordService
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_resources.services.files.transfer.constants import FETCH_TRANSFER_TYPE

from oarepo_runtime.proxies import current_runtime

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from flask_principal import Identity

log = logging.getLogger(__name__)

# Seconds to wait for a fetched (``transfer.type: F``) file to connect/respond.
FETCH_TIMEOUT = 60


class RecordLoader:
    """Create or update records of a model from fixture entries read from ``folder``."""

    def __init__(self, model_code: str, identity: Identity, folder: Path) -> None:
        """Initialize the loader; local file paths of the entries are relative to ``folder``."""
        self._model = current_runtime.models[model_code]
        self._identity = identity
        self._folder = folder

    def load(self, entry: dict[str, Any]) -> None:
        """Create or update a single record, logging a failure instead of raising.

        The pid is minted in ``PIDField.post_create`` via the field's provider
        (``RecordIdProviderV2.create`` calls ``generate_id``), not via the
        class-level context, so the provider is swapped while entries are being
        loaded to honour an entry's ``id``. Publishing a draft reuses the draft's
        pid, so only the class used by ``service.create`` needs patching.
        """
        service = self._model.service
        record_cls = service.draft_cls if isinstance(service, DraftRecordService) else service.record_cls
        with _fixture_id_provider_installed(record_cls.pid.field):
            try:
                self._create_or_update(entry)
            except Exception:
                log.exception("Failed to load %s fixture entry %s", self._model.code, entry.get("id", "<new>"))

    def _create_or_update(self, entry: dict[str, Any]) -> None:
        """Create or update a single record and publish it when the service supports drafts.

        An existing draft is updated in place; a published record without a draft
        is ``edit``-ed first. Files go through the model's (draft) file service
        before publishing.
        """
        service = self._model.service
        identity = self._identity
        entry = dict(entry)
        pid_value = entry.pop("id", None)
        files = entry.pop("files", None)
        file_entries = (files or {}).get("entries", [])
        if files is not None:
            entry["files"] = {"enabled": files.get("enabled", bool(file_entries))}
        if isinstance(service, DraftRecordService):
            if pid_value and _exists(service.read_draft, identity, pid_value):
                item = service.update_draft(identity, pid_value, entry)
            elif pid_value and _exists(service.read, identity, pid_value):
                service.edit(identity, pid_value)
                item = service.update_draft(identity, pid_value, entry)
            else:
                item = self._create(pid_value, entry)
            self._upload_files(self._model.draft_file_service, item.id, file_entries)
            service.publish(identity, item.id)
        else:
            if pid_value and _exists(service.read, identity, pid_value):
                item = service.update(identity, pid_value, entry)
            else:
                item = self._create(pid_value, entry)
            self._upload_files(self._model.file_service, item.id, file_entries)

    def _upload_files(self, file_service: Any, record_id: str, file_entries: list[dict[str, Any]]) -> None:
        """Sync the record's files with ``file_entries``, re-transferring only the changed ones."""
        if not file_entries:
            return
        identity = self._identity
        recorded = {f["key"]: f for f in file_service.list_files(identity, record_id).to_dict()["entries"]}
        changed = [f for f in file_entries if not self._is_recorded(f, recorded.get(f["key"]))]
        unchanged_keys = {f["key"] for f in file_entries} - {f["key"] for f in changed}
        if recorded.keys() - unchanged_keys or changed:
            files = file_service.record_cls.pid.resolve(record_id, registered_only=False).files
            if files.bucket.locked:
                # Editing a published record locks its draft's files (invenio wants
                # changes to go through a new version); fixtures change them in place.
                files.unlock()
        for key in recorded:
            if key not in unchanged_keys:
                file_service.delete_file(identity, record_id, key)
        if not changed:
            return
        file_service.init_files(identity, record_id, [_init_metadata(f) for f in changed])
        for f in changed:
            if "path" in f:
                path = self._folder / f["path"]
                with path.open("rb") as stream:
                    file_service.set_file_content(identity, record_id, f["key"], stream, path.stat().st_size)
            elif _is_fetch(f):
                # Fetched here rather than by the async fetch task, so the draft can be published right away.
                with requests.get(f["transfer"]["url"], stream=True, timeout=FETCH_TIMEOUT) as response:
                    response.raise_for_status()
                    # requests does not decode transport compression (gzip, ...) on the raw stream
                    response.raw.decode_content = True
                    file_service.set_file_content(identity, record_id, f["key"], response.raw, f.get("size"))
            else:
                continue
            file_service.commit_file(identity, record_id, f["key"])

    def _is_recorded(self, file_entry: dict[str, Any], recorded: dict[str, Any] | None) -> bool:
        """Return whether the recorded file has the entry's size and checksum."""
        if recorded is None:
            return False
        size, checksum = file_entry.get("size"), file_entry.get("checksum")
        if "path" in file_entry:
            path = self._folder / file_entry["path"]
            size = path.stat().st_size
            with path.open("rb") as stream:
                checksum = f"md5:{hashlib.file_digest(stream, 'md5').hexdigest()}"
        return None not in (size, checksum) and (size, checksum) == (recorded.get("size"), recorded.get("checksum"))

    def _create(self, pid_value: str | None, entry: dict[str, Any]) -> Any:
        """Create the record, minting ``pid_value`` as its pid when given."""
        token = _fixture_pid_value.set(pid_value)
        try:
            return self._model.service.create(self._identity, entry)
        finally:
            _fixture_pid_value.reset(token)


def _is_fetch(file_entry: dict[str, Any]) -> bool:
    return file_entry.get("transfer", {}).get("type") == FETCH_TRANSFER_TYPE


def _init_metadata(file_entry: dict[str, Any]) -> dict[str, Any]:
    """Return the metadata to initialize the file with; fetched files are initialized as local."""
    drop = {"path", "transfer"} if _is_fetch(file_entry) else {"path"}
    return {k: v for k, v in file_entry.items() if k not in drop}


def _exists(read: Callable[[Identity, str], Any], identity: Identity, pid_value: str) -> bool:
    """Return whether ``read`` finds the record/draft with the given pid."""
    try:
        read(identity, pid_value)
    except PIDDoesNotExistError:
        return False
    return True


_fixture_pid_value: ContextVar[str | None] = ContextVar("fixture_pid_value", default=None)


@cache
def _fixture_id_provider(provider: Any) -> type:
    """Subclass ``provider`` so that ``generate_id`` returns the fixture's ``id`` when set."""

    class FixtureIdProvider(provider):
        @classmethod
        def generate_id(cls, options: Any = None) -> str:
            return _fixture_pid_value.get() or super().generate_id(options)

    return FixtureIdProvider


_provider_lock = threading.Lock()
# id(pid field) -> (original provider, number of loads currently using the swapped one)
_provider_users: dict[int, tuple[Any, int]] = {}


@contextmanager
def _fixture_id_provider_installed(field: Any) -> Iterator[None]:
    """Swap the pid field's provider for the fixture one while any thread is inside.

    The first caller installs it and the last one restores the original. Callers
    in between share it, which is safe as the fixture ``id`` is read from a
    ``ContextVar`` (per thread) and the original ``generate_id`` is used when unset.
    """
    key = id(field)
    with _provider_lock:
        original, users = _provider_users.get(key, (field._provider, 0))  # noqa: SLF001
        if not users:
            field._provider = _fixture_id_provider(original)  # noqa: SLF001
        _provider_users[key] = (original, users + 1)
    try:
        yield
    finally:
        with _provider_lock:
            original, users = _provider_users.pop(key)
            if users == 1:
                field._provider = original  # noqa: SLF001
            else:
                _provider_users[key] = (original, users - 1)
