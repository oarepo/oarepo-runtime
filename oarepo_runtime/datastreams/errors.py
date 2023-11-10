# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Datastream errors."""
from typing import Union

from .json import JSONObject


class DataStreamError(Exception):
    def __init__(
        self,
        message,
        code=None,
        location=None,
        detail: Union[JSONObject, None] = None,
    ):
        """
        @param message: a string message (overview)
        @param code: a machine processable code
        @param location: location inside the json, where the error was detected. Using dot notation,
               arrays are indexed from 0, for example: `metadata.titles.0.language`
        @param detail: a json-serializable object (dictionary) with details
        """
        super().__init__(message)
        assert detail is None or isinstance(detail, dict)
        self.detail = detail
        self.message = message
        self.code = code
        self.location = location


class ReaderError(DataStreamError):
    """Transformer application exception."""


class TransformerError(DataStreamError):
    """Transformer application exception."""


class WriterError(DataStreamError):
    """Transformer application exception."""


class DataStreamCatalogueError(Exception):
    def __init__(self, message, entry=None, stream_name=None) -> None:
        super().__init__(message)
        self.entry = entry
        self.stream_name = stream_name
