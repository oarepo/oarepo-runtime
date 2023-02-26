# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 CERN.
#
# Invenio-Vocabularies is free software; you can redistribute it and/or
# modify it under the terms of the MIT License; see LICENSE file for more
# details.

"""Datastream errors."""


class ReaderError(Exception):
    """Transformer application exception."""


class TransformerError(Exception):
    """Transformer application exception."""


class WriterError(Exception):
    """Transformer application exception."""


class DataStreamCatalogueError(Exception):
    def __init__(self, message, entry=None, stream_name=None) -> None:
        super().__init__(message)
        self.entry = entry
        self.stream_name = stream_name
