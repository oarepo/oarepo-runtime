from __future__ import annotations

import pytest
from invenio_drafts_resources.records.api import Draft, Record
from invenio_records_resources.proxies import current_service_registry
from invenio_records_resources.records.api import RecordBase
from invenio_vocabularies.records.api import Vocabulary

from oarepo_runtime import current_runtime
from oarepo_runtime.api import Model


class TestConfig:
    """Test configuration for the Model."""

    record_cls = Record
    draft_cls = Draft


class TestService:
    """Test service for the Model."""

    config = TestConfig()


def test_model():
    m = Model(
        name="test",
        version="1.0.0",
        service=TestService(),
        global_search_enabled=True,
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
        name="test",
        version="1.0.0",
        service=service_instance,
        service_config=config_instance,
        record=record,
        draft=draft,
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
    assert vocabulary_model.name == "vocabularies"

    assert vocabulary_model.record_cls is Vocabulary
    assert vocabulary_model.draft_cls is None
    assert vocabulary_model.service is current_service_registry.get("vocabularies")
    assert (
        vocabulary_model.service_config
        is current_service_registry.get("vocabularies").config
    )

    assert current_runtime.models_by_record_class is not None
    assert Vocabulary in current_runtime.models_by_record_class

    assert current_runtime.get_record_service_for_record_class(
        Vocabulary
    ) is current_service_registry.get("vocabularies")

    with pytest.raises(KeyError, match="No service found for record class 'Record'."):
        current_runtime.get_record_service_for_record_class(RecordBase)

    with pytest.raises(KeyError, match="No service found for record class 'object'."):
        current_runtime.get_record_service_for_record_class(object)

    with pytest.raises(ValueError, match="Need to pass a record instance, got None"):
        current_runtime.get_record_service_for_record(None)

    assert current_runtime.get_record_service_for_record(
        Vocabulary({})
    ) is current_service_registry.get("vocabularies")
