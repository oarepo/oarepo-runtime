#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see https://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test typing module."""

from __future__ import annotations

import json

from oarepo_runtime.resources.signposting import datacite_to_signposting_links


def test_datacite_to_signposting():
    datacite_dict = json.load(open("tests/data/datacite_export.json"))
    signposting_links = datacite_to_signposting_links(datacite_dict)
    assert signposting_links == {'Link': '<https://orcid.org/0000-0001-5727-2427>; rel=author, '
         '<https://ror.org/04wxnsj81>; rel=author, '
         '<https://creativecommons.org/licenses/by/4.0/legalcode>; rel=type'}
