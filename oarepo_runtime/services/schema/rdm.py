import importlib.resources
import re
from functools import partial

import marshmallow as ma
from invenio_access.permissions import system_identity
from invenio_i18n import gettext as _
from invenio_i18n.selectors import get_locale
from invenio_rdm_records.services.schemas.metadata import (
    CreatorSchema,
    record_identifiers_schemes,
)
from invenio_rdm_records.services.schemas.tombstone import DeletionStatusSchema
from invenio_rdm_records.services.schemas.versions import VersionsSchema
from invenio_records_resources.proxies import current_service_registry
from invenio_vocabularies.contrib.awards.schema import AwardRelationSchema
from invenio_vocabularies.contrib.funders.schema import FunderRelationSchema
from marshmallow import fields as ma_fields
from marshmallow import pre_load
from marshmallow_utils.fields import (
    IdentifierSet,
)
from marshmallow_utils.fields.nestedattr import NestedAttribute
from marshmallow_utils.schemas.identifier import IdentifierSchema

from .i18n import MultilingualField


class RDMRecordMixin(ma.Schema):
    versions = NestedAttribute(VersionsSchema, dump_only=True)
    deletion_status = ma_fields.Nested(DeletionStatusSchema, dump_only=True)


class MultilingualAwardSchema(AwardRelationSchema):
    class Meta:
        unknown = ma.RAISE

    @pre_load()
    def convert_to_multilingual(self, data, many, **kwargs):
        if "title" in data and type(data["title"]) is str:
            lang = get_locale()
            data["title"] = {lang: data["title"]}
        return data


class FundingSchema(ma.Schema):
    """Funding schema."""

    funder = ma_fields.Nested(FunderRelationSchema, required=True)
    award = ma_fields.Nested(MultilingualAwardSchema)


class RecordIdentifierField(IdentifierSet):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ma.fields.Nested(
                partial(IdentifierSchema, allowed_schemes=record_identifiers_schemes)
            ),
            *args,
            **kwargs,
        )


class RelatedRecordIdentifierField(IdentifierSet):
    def __init__(self, *args, **kwargs):
        super().__init__(
            ma.fields.Nested(
                partial(IdentifierSchema, allowed_schemes=record_identifiers_schemes)
            ),
            *args,
            **kwargs,
        )


class RDMSubjectSchema(ma.Schema):
    """Subject ui schema."""

    class Meta:
        unknown = ma.RAISE

    _id = ma.fields.String(data_key="id")

    subject = MultilingualField()


class RDMNTKCreatorsSchema(CreatorSchema):
    """NTK version of RDM creators schema.

    This version makes sure that organizations are selected from the
    list of organizations in the system. Record will not be valid if
    organization is not in the system.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._load_organization_exceptions()

    def _load_organization_exceptions(self):
        """Load organization name exceptions from data file."""
        with importlib.resources.open_text(
            "oarepo_runtime.services.schema.data", "organization_exceptions.txt"
        ) as f:
            self.organization_exceptions = [line.strip() for line in f if line.strip()]

    def _is_organization_exception(self, name):
        """Check if organization name is in exceptions list."""
        return name in self.organization_exceptions

    @ma.validates_schema
    def check_organization_or_affiliation(self, data, **kwargs):
        """Check if organization is in the system."""
        person_or_org = data.get("person_or_org", {})
        if person_or_org.get("type") == "personal":
            affiliations = data.get("affiliations", [])
            for affiliation in affiliations:
                if not self.from_vocabulary(affiliation):
                    raise ma.ValidationError(
                        _(
                            "It is necessary to choose organization from the controlled vocabulary. "
                            "To add organization, please go to "
                            "https://nusl.techlib.cz/cs/migrace-nusl/navrh-novych-hesel/"
                        ),
                        field_name="affiliations",
                    )
        else:
            # organization
            name = person_or_org.get("name")
            affiliations = current_service_registry.get("affiliations")
            found = [
                x["name"]
                for x in affiliations.search(
                    system_identity,
                    q=f'name.suggest:"{escape_opensearch_query(name)}"',
                    size=100,
                ).hits
            ]
            if name not in found and not self._is_organization_exception(name):
                raise ma.ValidationError(
                    _(
                        "It is necessary to choose organization from the controlled vocabulary. "
                        "To add organization, please go to "
                        "https://nusl.techlib.cz/cs/migrace-nusl/navrh-novych-hesel/"
                    ),
                    field_name="person_or_org",
                )
        return data

    def from_vocabulary(self, affiliation):
        """Check if affiliation is from the vocabulary."""
        if "id" not in affiliation:
            return False
        return True


def escape_opensearch_query(value: str) -> str:
    """
    Escapes special characters in a string for safe use in OpenSearch query syntax.
    """
    # Escape each special character with a backslash
    escaped = re.sub(r'([\\+\-=&|><!(){}\[\]^"~*?:/])', r"\\\1", value)

    return escaped
