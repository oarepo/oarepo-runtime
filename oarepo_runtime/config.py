#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Config module."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from invenio_vocabularies import __version__ as vocabularies_version

from .api import Model

if TYPE_CHECKING:
    from collections.abc import Callable

    from flask import Flask


def build_config[T](config_class: type[T], app: Flask, *args: Any, **kwargs: Any) -> T:
    """Build the configuration for the service.

    This function is used to build the configuration for the service.
    """
    build_config: Callable[[Flask], T] | None = getattr(config_class, "build", None)
    if build_config is not None and callable(build_config):
        if args or kwargs:
            raise ValueError("Can not pass extra arguments when invenio ConfigMixin is used")
        return build_config(app)
    return config_class(*args, **kwargs)


#
# Configuration for the extension.
#

OAREPO_MODELS: dict[str, Model] = {
    # default invenio vocabularies
    "vocabularies": Model(
        name="vocabularies",
        version=vocabularies_version,
        service="vocabularies",
        description="Base (non-specialized) invenio vocabularies",
        records_alias_enabled=False,
        resource_config="invenio_vocabularies.resources.config.VocabulariesResourceConfig",
        resource="invenio_vocabularies.resources.resource.VocabulariesResource",
    ),
    # affiliations
    "affiliations": Model(
        name="affiliations",
        version=vocabularies_version,
        service="affiliations",
        description="Affiliations vocabulary",
        records_alias_enabled=False,
        resource_config="invenio_vocabularies.contrib.affiliations.resources.AffiliationsResourceConfig",
        resource="invenio_vocabularies.contrib.affiliations.resources.AffiliationsResource",
    ),
    # funders
    "funders": Model(
        name="funders",
        version=vocabularies_version,
        service="funders",
        description="Funders vocabulary",
        records_alias_enabled=False,
        resource_config="invenio_vocabularies.contrib.funders.resources.FundersResourceConfig",
        resource="invenio_vocabularies.contrib.funders.resources.FundersResource",
    ),
    # awards
    "awards": Model(
        name="awards",
        version=vocabularies_version,
        service="awards",
        description="Awards vocabulary",
        records_alias_enabled=False,
        resource_config="invenio_vocabularies.contrib.awards.resources.AwardsResourceConfig",
        resource="invenio_vocabularies.contrib.awards.resources.AwardsResource",
    ),
    # names
    "names": Model(
        name="names",
        version=vocabularies_version,
        service="names",
        description="Names vocabulary",
        records_alias_enabled=False,
        resource_config="invenio_vocabularies.contrib.names.resources.NamesResourceConfig",
        resource="invenio_vocabularies.contrib.names.resources.NamesResource",
    ),
    # subjects
    "subjects": Model(
        name="subjects",
        version=vocabularies_version,
        service="subjects",
        description="Subjects vocabulary",
        records_alias_enabled=False,
        resource_config="invenio_vocabularies.contrib.subjects.resources.SubjectsResourceConfig",
        resource="invenio_vocabularies.contrib.subjects.resources.SubjectsResource",
    ),
}
