# type: ignore  # noqa
#
# This file is part of Invenio.
# Copyright (C) 2020 CERN.
# Copyright (C) 2020 Northwestern University.
#
# Invenio-Drafts-Resources is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.
"""Example of a record draft API."""

from __future__ import annotations

from invenio_drafts_resources.records import Draft as DraftBase
from invenio_drafts_resources.records import ParentRecord as ParentRecordBase
from invenio_drafts_resources.records import Record as RecordBase
from invenio_drafts_resources.records.api import DraftRecordIdProviderV2
from invenio_drafts_resources.services.records.components.media_files import (
    MediaFilesAttrConfig,
)
from invenio_rdm_records.records.systemfields import HasDraftCheckField
from invenio_records.systemfields import ConstantField, ModelField, SystemField
from invenio_records_resources.records import FileRecord as FileRecordBase
from invenio_records_resources.records.systemfields import FilesField, IndexField
from invenio_records_resources.records.systemfields.pid import PIDField, PIDFieldContext

from oarepo_runtime.records.pid_providers import UniversalPIDMixin
from oarepo_runtime.records.systemfields import (
    MappingSystemFieldMixin,
    PublicationStatusSystemField,
)

from .models import (
    DraftMetadata,
    FileDraftMetadata,
    FileRecordMetadata,
    MediaFileDraftMetadata,
    MediaFileRecordMetadata,
    ParentRecordMetadata,
    ParentState,
    RecordMetadata,
)


class PIDProvider(UniversalPIDMixin, DraftRecordIdProviderV2):
    """Universal PID provider for mock records."""

    pid_type = "rcrds"


class ParentRecord(ParentRecordBase):  # type: ignore[misc]
    """Example parent record."""

    # Configuration
    model_cls = ParentRecordMetadata

    # System fields
    schema = ConstantField("$schema", "local://records/parent-v1.0.0.json")


class FileRecord(FileRecordBase):  # type: ignore[misc]
    """Example record file API."""

    model_cls = FileRecordMetadata
    record_cls = None  # defined below


class MediaFileRecord(FileRecordBase):  # type: ignore[misc]
    """Example record file API."""

    model_cls = MediaFileRecordMetadata
    record_cls = None  # defined below


class TestMappingSystemField(MappingSystemFieldMixin, SystemField):
    """Test mapping system field."""

    @property
    def mapping(self) -> dict:
        """Return the default mapping for the system field."""
        return {"test_field": {"type": "keyword"}}

    @property
    def mapping_settings(self) -> dict:
        """Return the default mapping settings for the system field."""
        return {"analysis": {"analyzers": {"test_analyzer": {"type": "custom", "tokenizer": "standard"}}}}


class FileDraft(FileRecordBase):
    """Example record file API."""

    model_cls = FileDraftMetadata
    record_cls = None  # defined below


class MediaFileDraft(FileRecordBase):
    """File associated with a draft."""

    model_cls = MediaFileDraftMetadata
    record_cls = None  # defined below


class Draft(DraftBase):
    """Example record API."""

    # Configuration
    model_cls = DraftMetadata
    versions_model_cls = ParentState
    parent_record_cls = ParentRecord

    pid = PIDField(provider=PIDProvider, context_cls=PIDFieldContext, create=True, delete=False)

    # System fields
    schema = ConstantField("$schema", "local://records/record-v1.0.0.json")

    index = IndexField("draftsresources-draft-v1.0.0", search_alias="draftsresources")

    files = FilesField(
        store=False,
        file_cls=FileDraft,
        dump=False,
        # Don't delete, we'll manage in the service
        delete=False,
    )

    media_files = FilesField(
        key=MediaFilesAttrConfig["_files_attr_key"],
        bucket_id_attr=MediaFilesAttrConfig["_files_bucket_id_attr_key"],
        bucket_attr=MediaFilesAttrConfig["_files_bucket_attr_key"],
        store=False,
        dump=False,
        file_cls=MediaFileDraft,
        # Don't delete, we'll manage in the service
        delete=False,
    )

    bucket_id = ModelField(dump=False)

    bucket = ModelField(dump=False)

    media_bucket_id = ModelField(dump=False)

    media_bucket = ModelField(dump=False)

    status = PublicationStatusSystemField()

    test_fld = TestMappingSystemField()

    has_draft = HasDraftCheckField()


class Record(RecordBase):  # type: ignore[misc]
    """Example record API."""

    # Configuration
    model_cls = RecordMetadata
    versions_model_cls = ParentState
    parent_record_cls = ParentRecord

    pid = PIDField(provider=PIDProvider, context_cls=PIDFieldContext, create=True)

    # System fields
    schema = ConstantField("$schema", "local://records/record-v1.0.0.json")

    index = IndexField("draftsresources-record-v1.0.0")

    files = FilesField(
        store=False,
        dump=True,
        file_cls=FileRecord,
        # Don't create
        create=False,
        # Don't delete, we'll manage in the service
        delete=False,
    )

    media_files = FilesField(
        key=MediaFilesAttrConfig["_files_attr_key"],
        bucket_id_attr=MediaFilesAttrConfig["_files_bucket_id_attr_key"],
        bucket_attr=MediaFilesAttrConfig["_files_bucket_attr_key"],
        store=False,
        dump=False,
        file_cls=MediaFileRecord,
        # Don't create
        create=False,
        # Don't delete, we'll manage in the service
        delete=False,
    )

    bucket_id = ModelField(dump=False)

    bucket = ModelField(dump=False)

    media_bucket_id = ModelField(dump=False)

    media_bucket = ModelField(dump=False)

    status = PublicationStatusSystemField()

    test_fld = TestMappingSystemField()

    has_draft = HasDraftCheckField(Draft)


class RecordMediaFiles(Record):  # type: ignore[misc]
    """Media file record API."""

    files = FilesField(
        key=MediaFilesAttrConfig["_files_attr_key"],
        bucket_id_attr=MediaFilesAttrConfig["_files_bucket_id_attr_key"],
        bucket_attr=MediaFilesAttrConfig["_files_bucket_attr_key"],
        store=False,
        dump=False,
        file_cls=MediaFileRecord,
        # Don't create
        create=False,
        # Don't delete, we'll manage in the service
        delete=False,
    )


FileRecord.record_cls = Record
MediaFileRecord.record_cls = RecordMediaFiles


class DraftMediaFiles(Draft):
    """RDM Draft media file API."""

    files = FilesField(
        key=MediaFilesAttrConfig["_files_attr_key"],
        bucket_id_attr=MediaFilesAttrConfig["_files_bucket_id_attr_key"],
        bucket_attr=MediaFilesAttrConfig["_files_bucket_attr_key"],
        store=False,
        dump=False,
        file_cls=MediaFileDraft,
        # Don't delete, we'll manage in the service
        delete=False,
    )


FileDraft.record_cls = Draft
MediaFileDraft.record_cls = DraftMediaFiles
