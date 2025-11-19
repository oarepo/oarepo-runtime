#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

from __future__ import annotations

from uuid import uuid4

import pytest
from invenio_drafts_resources.records.api import Draft, Record
from invenio_pidstore.errors import PIDDoesNotExistError
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.records.api import RecordBase
from invenio_records_resources.services.files import FileService
from invenio_vocabularies.records.api import Vocabulary
from invenio_vocabularies.resources.config import VocabulariesResourceConfig
from invenio_vocabularies.resources.resource import VocabulariesResource

from oarepo_runtime import current_runtime
from oarepo_runtime.api import Model


class TestConfig:
    """Test configuration for the Model."""

    record_cls = Record
    draft_cls = Draft


class TestService:
    """Test service for the Model."""

    config = TestConfig()


def test_ext_init_without_app():
    from oarepo_runtime.ext import OARepoRuntime

    OARepoRuntime()


def test_model():
    m = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=TestService(),
        resource_config="invenio_records_resources.resources.records.config.RecordResourceConfig",
        records_alias_enabled=True,
    )
    assert m.name == "test"
    assert m.version == "1.0.0"
    assert isinstance(m.service, TestService)
    assert isinstance(m.service.config, TestConfig)
    assert m.record_cls is Record
    assert m.draft_cls is Draft


def test_model_direct_instances():
    service_instance = TestService()
    config_instance = TestConfig()
    record = Record
    draft = Draft

    m = Model(
        code="test",
        name="test",
        version="1.0.0",
        service=service_instance,
        service_config=config_instance,
        record=record,
        draft=draft,
        resource_config="invenio_records_resources.resources.records.config.RecordResourceConfig",
    )

    assert m.service is service_instance
    assert m.service_config is config_instance
    assert m.record_cls is record
    assert m.draft_cls is draft


def test_ext_loaded(app, search_with_field_mapping, search_clear):
    assert "oarepo-runtime" in app.extensions
    assert current_runtime is not None

    models = current_runtime.models
    assert isinstance(models, dict)
    assert len(models) > 0
    assert "vocabularies" in models

    vocabulary_model = models["vocabularies"]
    assert vocabulary_model.code == "vocabularies"

    assert vocabulary_model.record_cls is Vocabulary
    assert vocabulary_model.draft_cls is None
    assert vocabulary_model.service is current_service_registry.get("vocabularies")
    assert vocabulary_model.service_config is current_service_registry.get("vocabularies").config

    assert current_runtime.models_by_record_class is not None
    assert Vocabulary in current_runtime.models_by_record_class

    assert current_runtime.get_record_service_for_record_class(Vocabulary) is current_service_registry.get(
        "vocabularies"
    )

    with pytest.raises(KeyError, match=r"No service found for record class 'Record'."):
        current_runtime.get_record_service_for_record_class(RecordBase)

    with pytest.raises(KeyError, match=r"No service found for record class 'object'."):
        current_runtime.get_record_service_for_record_class(object)

    with pytest.raises(ValueError, match=r"Need to pass a record instance, got None"):
        current_runtime.get_record_service_for_record(None)

    assert current_runtime.get_record_service_for_record(Vocabulary({})) is current_service_registry.get("vocabularies")

    vocabularies_model = current_runtime.models["vocabularies"]
    assert vocabularies_model.exports == []
    assert vocabularies_model.resource_config is not None
    assert isinstance(vocabularies_model.resource_config, VocabulariesResourceConfig)
    assert isinstance(vocabularies_model.resource, VocabulariesResource)

    assert "application/json" in vocabularies_model.response_handlers


def test_rdm_models_only_records_alias_enabled(app):
    from oarepo_runtime import current_runtime

    codes = {m.code for m in current_runtime.rdm_models}
    # Only the mock model is records-alias-enabled in tests
    assert codes == {"mock"}

    assert len(current_runtime.rdm_models) < len(current_runtime.models)


def test_pid_type_mappings(app):
    mock_model = current_runtime.models["mock"]

    assert mock_model.record_pid_type == "rcrds"
    assert mock_model.draft_pid_type == "rcrds"

    # record_class_by_pid_type
    rmap = current_runtime.record_class_by_pid_type
    assert "rcrds" in rmap
    assert rmap["rcrds"] is mock_model.record_cls

    # draft_class_by_pid_type
    dmap = current_runtime.draft_class_by_pid_type
    assert "rcrds" in dmap
    assert dmap["rcrds"] is mock_model.draft_cls

    # model_by_pid_type
    mmap = current_runtime.model_by_pid_type
    assert "rcrds" in mmap
    assert mmap["rcrds"] is mock_model


def test_schema_mappings(app):
    mock_model = current_runtime.models["mock"]
    mock_schema = mock_model.record_cls.schema.value  # type: ignore[attr-defined]

    ms = current_runtime.models_by_schema
    assert mock_schema in ms
    assert ms[mock_schema] is mock_model

    ms = current_runtime.rdm_models_by_schema
    assert mock_schema in ms
    assert ms[mock_schema] is mock_model

    assert len(current_runtime.rdm_models_by_schema) < len(current_runtime.models_by_schema)


def test_find_pid_helpers(app, db, search_with_field_mapping, service, search_clear, identity_simple, location):
    from oarepo_runtime import current_runtime

    created = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "PID test"},
            "files": {"enabled": False},
        },
    )

    # created.id is the PID value (DraftRecordIdProviderV2)
    pid_value = created.id
    draft = created._record  # noqa: SLF001 - access for test

    # find_pid_type_from_pid
    pid_type = current_runtime.find_pid_type_from_pid(pid_value)
    assert pid_type == "rcrds"

    # find_pid_from_uuid
    pid_obj = current_runtime.find_pid_from_uuid(draft.id)
    assert pid_obj.pid_type == "rcrds"
    assert pid_obj.pid_value == pid_value

    # non-existing pid
    with pytest.raises(
        PIDDoesNotExistError,
        match=r"The pid value/record uuid is not associated with any record.",
    ):
        current_runtime.find_pid_from_uuid(uuid4())

    with pytest.raises(
        PIDDoesNotExistError,
        match=r"The pid value/record uuid is not associated with any record.",
    ):
        current_runtime.find_pid_type_from_pid("abcde-fghij-012")


def test_indices(app):
    mock_model = current_runtime.models["mock"]

    published_indices = current_runtime.published_indices
    draft_indices = current_runtime.draft_indices

    assert mock_model.record_cls.index.search_alias in published_indices  # type: ignore[attr-defined]
    assert mock_model.draft_cls.index.search_alias in draft_indices  # type: ignore[attr-defined]

    assert len(published_indices) == 1
    assert len(draft_indices) == 1


def test_get_file_service_from_api_record(app, service, identity_simple):
    created = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "PID test"},
            "files": {"enabled": False},
        },
    )

    file_service = current_runtime.get_file_service_for_record(created._record)  # noqa: SLF001
    assert isinstance(file_service, FileService)


def test_get_file_service_for_record_keyerror(app):
    class UnknownRecord:
        pass

    unknown_record = UnknownRecord()
    with pytest.raises(KeyError, match=r"No model found for record class 'UnknownRecord'."):
        current_runtime.get_file_service_for_record(unknown_record)


def test_get_file_service_for_published_record(app, service, identity_simple):
    created = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "PID test"},
            "files": {"enabled": False},
        },
    )
    # Simulate published record
    created._record.is_draft = False  # noqa: SLF001
    file_service = current_runtime.get_file_service_for_record(created._record)  # noqa: SLF001
    assert isinstance(file_service, FileService)


def test_get_model_for_record(app, service, identity_simple):
    created = service.create(
        identity=identity_simple,
        data={
            "metadata": {"title": "PID test"},
            "files": {"enabled": False},
        },
    )
    # Simulate published record
    created._record.is_draft = False  # noqa: SLF001
    model = current_runtime.get_model_for_record(record=created._record)  # noqa: SLF001
    assert isinstance(model, Model)


def test_get_model_for_record_value_error(app):
    with pytest.raises(ValueError, match=r"Need to pass a record instance, got None"):
        current_runtime.get_model_for_record(record=None)
