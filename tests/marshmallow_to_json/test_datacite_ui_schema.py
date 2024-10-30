import marshmallow as ma
from marshmallow import fields as ma_fields, Schema
from marshmallow.validate import OneOf
from oarepo_runtime.services.schema.marshmallow import DictOnlySchema
from oarepo_runtime.services.schema.ui import LocalizedEDTFTime

from oarepo_runtime.services.schema.marshmallow_to_json_schema import marshmallow_to_json_schema

#TODO more testing on other schemas

class NRDataCiteMetadataUISchema(Schema):

    alternateIdentifiers = ma_fields.List(
        ma_fields.Nested(lambda: AlternateIdentifierUISchema())
    )

    container = ma_fields.Nested(lambda: ContainerUISchema())

    contributors = ma_fields.List(ma_fields.Nested(lambda: ContributorUISchema()))

    creators = ma_fields.List(ma_fields.Nested(lambda: CreatorUISchema()))

    dates = ma_fields.List(ma_fields.Nested(lambda: DateUISchema()))

    descriptions = ma_fields.List(ma_fields.Nested(lambda: DescriptionUISchema()))

    doi = ma_fields.String()

    formats = ma_fields.List(ma_fields.String())

    fundingReferences = ma_fields.List(
        ma_fields.Nested(lambda: FundingReferenceUISchema())
    )

    geoLocations = ma_fields.List(ma_fields.Nested(lambda: GeoLocationUISchema()))

    language = ma_fields.String()

    publicationYear = ma_fields.String()

    publisher = ma_fields.Nested(lambda: PublisherUISchema())

    relatedIdentifiers = ma_fields.List(
        ma_fields.Nested(lambda: RelatedIdentifierUISchema())
    )

    relatedItems = ma_fields.List(ma_fields.Nested(lambda: RelatedItemUISchema()))

    resourceType = ma_fields.Nested(lambda: ResourceTypeUISchema())

    rightsList = ma_fields.List(ma_fields.Nested(lambda: RightsUISchema()))

    schemaVersion = ma_fields.String()

    sizes = ma_fields.List(ma_fields.String())

    subjects = ma_fields.List(ma_fields.Nested(lambda: SubjectUISchema()))

    titles = ma_fields.List(ma_fields.Nested(lambda: TitleUISchema()))

    url = ma_fields.String()

    version = ma_fields.String()


class GeoLocationUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    geoLocationBox = ma_fields.Nested(lambda: GeoLocationBoxUISchema())

    geoLocationPlace = ma_fields.String()

    geoLocationPoint = ma_fields.Nested(lambda: GeoLocationPointUISchema())

    geoLocationPolygons = ma_fields.List(
        ma_fields.Nested(lambda: GeoLocationPolygonUISchema())
    )


class RelatedItemUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    contributors = ma_fields.List(ma_fields.Nested(lambda: ContributorUISchema()))

    creators = ma_fields.List(ma_fields.Nested(lambda: CreatorUISchema()))

    edition = ma_fields.String()

    firstPage = ma_fields.String()

    issue = ma_fields.String()

    lastPage = ma_fields.String()

    number = ma_fields.String()

    numberType = ma_fields.String(
        validate=[OneOf(["Article", "Chapter", "Report", "Other"])]
    )

    publicationYear = ma_fields.String()

    publisher = ma_fields.String()

    relatedItemIdentifier = ma_fields.Nested(
        lambda: RelatedItemIdentifierUISchema(), required=True
    )

    relatedItemType = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "Audiovisual",
                    "Book",
                    "BookChapter",
                    "Collection",
                    "ComputationalNotebook",
                    "ConferencePaper",
                    "ConferenceProceeding",
                    "DataPaper",
                    "Dataset",
                    "Dissertation",
                    "Event",
                    "Image",
                    "Instrument",
                    "InteractiveResource",
                    "Journal",
                    "JournalArticle",
                    "Model",
                    "OutputManagementPlan",
                    "PeerReview",
                    "PhysicalObject",
                    "Preprint",
                    "Report",
                    "Service",
                    "Software",
                    "Sound",
                    "Standard",
                    "StudyRegistration",
                    "Text",
                    "Workflow",
                    "Other",
                ]
            )
        ],
    )

    relatedMetadataScheme = ma_fields.String()

    relationType = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "IsCitedBy",
                    "Cites",
                    "IsCollectedBy",
                    "Collects",
                    "IsSupplementTo",
                    "IsSupplementedBy",
                    "IsContinuedBy",
                    "Continues",
                    "IsDescribedBy",
                    "Describes",
                    "HasMetadata",
                    "IsMetadataFor",
                    "HasVersion",
                    "IsVersionOf",
                    "IsNewVersionOf",
                    "IsPartOf",
                    "IsPreviousVersionOf",
                    "IsPublishedIn",
                    "HasPart",
                    "IsReferencedBy",
                    "References",
                    "IsDocumentedBy",
                    "Documents",
                    "IsCompiledBy",
                    "Compiles",
                    "IsVariantFormOf",
                    "IsOriginalFormOf",
                    "IsIdenticalTo",
                    "IsReviewedBy",
                    "Reviews",
                    "IsDerivedFrom",
                    "IsSourceOf",
                    "IsRequiredBy",
                    "Requires",
                    "IsObsoletedBy",
                    "Obsoletes",
                ]
            )
        ],
    )

    resourceTypeGeneral = ma_fields.String(
        validate=[
            OneOf(
                [
                    "Audiovisual",
                    "Book",
                    "BookChapter",
                    "Collection",
                    "ComputationalNotebook",
                    "ConferencePaper",
                    "ConferenceProceeding",
                    "DataPaper",
                    "Dataset",
                    "Dissertation",
                    "Event",
                    "Image",
                    "Instrument",
                    "InteractiveResource",
                    "Journal",
                    "JournalArticle",
                    "Model",
                    "OutputManagementPlan",
                    "PeerReview",
                    "PhysicalObject",
                    "Preprint",
                    "Report",
                    "Service",
                    "Software",
                    "Sound",
                    "Standard",
                    "StudyRegistration",
                    "Text",
                    "Workflow",
                    "Other",
                ]
            )
        ]
    )

    schemeType = ma_fields.String()

    schemeURI = ma_fields.String()

    titles = ma_fields.List(
        ma_fields.Nested(lambda: RelatedItemTitleUISchema()), required=True
    )

    volume = ma_fields.String()


class ContributorUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    affiliation = ma_fields.List(ma_fields.Nested(lambda: AffiliationUISchema()))

    contributorType = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "ContactPerson",
                    "DataCollector",
                    "DataCurator",
                    "DataManager",
                    "Distributor",
                    "Editor",
                    "HostingInstitution",
                    "Producer",
                    "ProjectLeader",
                    "ProjectManager",
                    "ProjectMember",
                    "RegistrationAgency",
                    "RegistrationAuthority",
                    "RelatedPerson",
                    "Researcher",
                    "ResearchGroup",
                    "RightsHolder",
                    "Sponsor",
                    "Supervisor",
                    "WorkPackageLeader",
                    "Other",
                ]
            )
        ],
    )

    familyName = ma_fields.String()

    givenName = ma_fields.String()

    lang = ma_fields.String()

    name = ma_fields.String(required=True)

    nameIdentifiers = ma_fields.List(ma_fields.Nested(lambda: NameIdentifierUISchema()))

    nameType = ma_fields.String(validate=[OneOf(["Organizational", "Personal"])])


class CreatorUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    affiliation = ma_fields.List(ma_fields.Nested(lambda: AffiliationUISchema()))

    familyName = ma_fields.String()

    givenName = ma_fields.String()

    lang = ma_fields.String()

    name = ma_fields.String(required=True)

    nameIdentifiers = ma_fields.List(ma_fields.Nested(lambda: NameIdentifierUISchema()))

    nameType = ma_fields.String(validate=[OneOf(["Organizational", "Personal"])])


class GeoLocationPolygonUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    inPolygonPoint = ma_fields.Nested(lambda: GeoLocationPointUISchema())

    polygonPoints = ma_fields.List(
        ma_fields.Nested(lambda: GeoLocationPointUISchema()), required=True
    )


class AffiliationUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    affiliationIdentifier = ma_fields.String()

    affiliationIdentifierScheme = ma_fields.String()

    name = ma_fields.String(required=True)

    schemeURI = ma_fields.String()


class AlternateIdentifierUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    alternateIdentifier = ma_fields.String(required=True)

    alternateIdentifierType = ma_fields.String(required=True)


class ContainerUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    firstPage = ma_fields.String()

    title = ma_fields.String()

    type = ma_fields.String()


class DateUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    date = LocalizedEDTFTime(required=True)

    dateInformation = ma_fields.String()

    dateType = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "Accepted",
                    "Available",
                    "Copyrighted",
                    "Collected",
                    "Created",
                    "Issued",
                    "Submitted",
                    "Updated",
                    "Valid",
                    "Withdrawn",
                    "Other",
                ]
            )
        ],
    )


class DescriptionUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    description = ma_fields.String(required=True)

    descriptionType = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "Abstract",
                    "Methods",
                    "SeriesInformation",
                    "TableOfContents",
                    "TechnicalInfo",
                    "Other",
                ]
            )
        ],
    )

    lang = ma_fields.String()


class FundingReferenceUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    awardNumber = ma_fields.String()

    awardTitle = ma_fields.String()

    awardURI = ma_fields.String()

    funderIdentifier = ma_fields.String()

    funderIdentifierType = ma_fields.String(
        validate=[OneOf(["ISNI", "GRID", "Crossref Funder ID", "ROR", "Other"])]
    )

    funderName = ma_fields.String(required=True)


class GeoLocationBoxUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    eastBoundLongitude = ma_fields.Float(required=True)

    northBoundLatitude = ma_fields.Float(required=True)

    southBoundLatitude = ma_fields.Float(required=True)

    westBoundLongitude = ma_fields.Float(required=True)


class GeoLocationPointUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    pointLatitude = ma_fields.Float()

    pointLongitude = ma_fields.Float()


class NameIdentifierUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    nameIdentifier = ma_fields.String(required=True)

    nameIdentifierScheme = ma_fields.String(required=True)

    schemeURI = ma_fields.String()


class PublisherUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    lang = ma_fields.String()

    name = ma_fields.String(required=True)

    publisherIdentifier = ma_fields.String()

    publisherIdentifierScheme = ma_fields.String()

    schemeURI = ma_fields.String()


class RelatedIdentifierUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    relatedIdentifier = ma_fields.String()

    relatedIdentifierType = ma_fields.String(
        validate=[
            OneOf(
                [
                    "ARK",
                    "arXiv",
                    "bibcode",
                    "DOI",
                    "EAN13",
                    "EISSN",
                    "Handle",
                    "IGSN",
                    "ISBN",
                    "ISSN",
                    "ISTC",
                    "LISSN",
                    "LSID",
                    "PMID",
                    "PURL",
                    "UPC",
                    "URL",
                    "URN",
                    "w3id",
                ]
            )
        ]
    )

    relatedMetadataScheme = ma_fields.String()

    relationType = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "IsCitedBy",
                    "Cites",
                    "IsCollectedBy",
                    "Collects",
                    "IsSupplementTo",
                    "IsSupplementedBy",
                    "IsContinuedBy",
                    "Continues",
                    "IsDescribedBy",
                    "Describes",
                    "HasMetadata",
                    "IsMetadataFor",
                    "HasVersion",
                    "IsVersionOf",
                    "IsNewVersionOf",
                    "IsPartOf",
                    "IsPreviousVersionOf",
                    "IsPublishedIn",
                    "HasPart",
                    "IsReferencedBy",
                    "References",
                    "IsDocumentedBy",
                    "Documents",
                    "IsCompiledBy",
                    "Compiles",
                    "IsVariantFormOf",
                    "IsOriginalFormOf",
                    "IsIdenticalTo",
                    "IsReviewedBy",
                    "Reviews",
                    "IsDerivedFrom",
                    "IsSourceOf",
                    "IsRequiredBy",
                    "Requires",
                    "IsObsoletedBy",
                    "Obsoletes",
                ]
            )
        ],
    )

    resourceTypeGeneral = ma_fields.String(
        validate=[
            OneOf(
                [
                    "Audiovisual",
                    "Book",
                    "BookChapter",
                    "Collection",
                    "ComputationalNotebook",
                    "ConferencePaper",
                    "ConferenceProceeding",
                    "DataPaper",
                    "Dataset",
                    "Dissertation",
                    "Event",
                    "Image",
                    "Instrument",
                    "InteractiveResource",
                    "Journal",
                    "JournalArticle",
                    "Model",
                    "OutputManagementPlan",
                    "PeerReview",
                    "PhysicalObject",
                    "Preprint",
                    "Report",
                    "Service",
                    "Software",
                    "Sound",
                    "Standard",
                    "StudyRegistration",
                    "Text",
                    "Workflow",
                    "Other",
                ]
            )
        ]
    )

    schemeType = ma_fields.String()

    schemeURI = ma_fields.String()


class RelatedItemIdentifierUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    relatedItemIdentifier = ma_fields.String(required=True)

    relatedItemIdentifierType = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "ARK",
                    "arXiv",
                    "bibcode",
                    "DOI",
                    "EAN13",
                    "EISSN",
                    "Handle",
                    "IGSN",
                    "ISBN",
                    "ISSN",
                    "ISTC",
                    "LISSN",
                    "LSID",
                    "PMID",
                    "PURL",
                    "UPC",
                    "URL",
                    "URN",
                    "w3id",
                ]
            )
        ],
    )


class RelatedItemTitleUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    lang = ma_fields.String()

    title = ma_fields.String(required=True)

    titleType = ma_fields.String(
        validate=[OneOf(["AlternativeTitle", "Subtitle", "TranslatedTitle", "Other"])]
    )


class ResourceTypeUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    resourceType = ma_fields.String()

    resourceTypeGeneral = ma_fields.String(
        required=True,
        validate=[
            OneOf(
                [
                    "Audiovisual",
                    "Book",
                    "BookChapter",
                    "Collection",
                    "ComputationalNotebook",
                    "ConferencePaper",
                    "ConferenceProceeding",
                    "DataPaper",
                    "Dataset",
                    "Dissertation",
                    "Event",
                    "Image",
                    "Instrument",
                    "InteractiveResource",
                    "Journal",
                    "JournalArticle",
                    "Model",
                    "OutputManagementPlan",
                    "PeerReview",
                    "PhysicalObject",
                    "Preprint",
                    "Report",
                    "Service",
                    "Software",
                    "Sound",
                    "Standard",
                    "StudyRegistration",
                    "Text",
                    "Workflow",
                    "Other",
                ]
            )
        ],
    )


class RightsUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    lang = ma_fields.String()

    rights = ma_fields.String()

    rightsIdentifier = ma_fields.String()

    rightsIdentifierScheme = ma_fields.String()

    rightsURI = ma_fields.String()

    schemeURI = ma_fields.String()


class SubjectUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    classificationCode = ma_fields.String()

    lang = ma_fields.String()

    schemeURI = ma_fields.String()

    subject = ma_fields.String(required=True)

    subjectScheme = ma_fields.String()

    valueURI = ma_fields.String()


class TitleUISchema(DictOnlySchema):
    class Meta:
        unknown = ma.RAISE

    lang = ma_fields.String()

    title = ma_fields.String(required=True)

    titleType = ma_fields.String(
        validate=[OneOf(["AlternativeTitle", "Subtitle", "TranslatedTitle", "Other"])]
    )


def test_NRDataCiteMetadataUISchema():
    schema = NRDataCiteMetadataUISchema()
    converted = marshmallow_to_json_schema(schema)

    print(converted)
    assert converted == {
            "type": "object",
            "properties": {
                "alternateIdentifiers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "alternateIdentifier": {
                                "type": "string"
                            },
                            "alternateIdentifierType": {
                                "type": "string"
                            }
                        }
                    }
                },
                "container": {
                    "type": "object",
                    "properties": {
                        "firstPage": {
                            "type": "string"
                        },
                        "title": {
                            "type": "string"
                        },
                        "type": {
                            "type": "string"
                        }
                    }
                },
                "contributors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "affiliation": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "affiliationIdentifier": {
                                            "type": "string"
                                        },
                                        "affiliationIdentifierScheme": {
                                            "type": "string"
                                        },
                                        "name": {
                                            "type": "string"
                                        },
                                        "schemeURI": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "contributorType": {
                                "type": "string"
                            },
                            "familyName": {
                                "type": "string"
                            },
                            "givenName": {
                                "type": "string"
                            },
                            "lang": {
                                "type": "string"
                            },
                            "name": {
                                "type": "string"
                            },
                            "nameIdentifiers": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "nameIdentifier": {
                                            "type": "string"
                                        },
                                        "nameIdentifierScheme": {
                                            "type": "string"
                                        },
                                        "schemeURI": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "nameType": {
                                "type": "string"
                            }
                        }
                    }
                },
                "creators": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "affiliation": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "affiliationIdentifier": {
                                            "type": "string"
                                        },
                                        "affiliationIdentifierScheme": {
                                            "type": "string"
                                        },
                                        "name": {
                                            "type": "string"
                                        },
                                        "schemeURI": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "familyName": {
                                "type": "string"
                            },
                            "givenName": {
                                "type": "string"
                            },
                            "lang": {
                                "type": "string"
                            },
                            "name": {
                                "type": "string"
                            },
                            "nameIdentifiers": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "nameIdentifier": {
                                            "type": "string"
                                        },
                                        "nameIdentifierScheme": {
                                            "type": "string"
                                        },
                                        "schemeURI": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "nameType": {
                                "type": "string"
                            }
                        }
                    }
                },
                "dates": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "date": {
                                "type": "string",
                                "format": "date-time"
                            },
                            "dateInformation": {
                                "type": "string"
                            },
                            "dateType": {
                                "type": "string"
                            }
                        }
                    }
                },
                "descriptions": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "description": {
                                "type": "string"
                            },
                            "descriptionType": {
                                "type": "string"
                            },
                            "lang": {
                                "type": "string"
                            }
                        }
                    }
                },
                "doi": {
                    "type": "string"
                },
                "formats": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "fundingReferences": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "awardNumber": {
                                "type": "string"
                            },
                            "awardTitle": {
                                "type": "string"
                            },
                            "awardURI": {
                                "type": "string"
                            },
                            "funderIdentifier": {
                                "type": "string"
                            },
                            "funderIdentifierType": {
                                "type": "string"
                            },
                            "funderName": {
                                "type": "string"
                            }
                        }
                    }
                },
                "geoLocations": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "geoLocationBox": {
                                "type": "object",
                                "properties": {
                                    "eastBoundLongitude": {
                                        "type": "number"
                                    },
                                    "northBoundLatitude": {
                                        "type": "number"
                                    },
                                    "southBoundLatitude": {
                                        "type": "number"
                                    },
                                    "westBoundLongitude": {
                                        "type": "number"
                                    }
                                }
                            },
                            "geoLocationPlace": {
                                "type": "string"
                            },
                            "geoLocationPoint": {
                                "type": "object",
                                "properties": {
                                    "pointLatitude": {
                                        "type": "number"
                                    },
                                    "pointLongitude": {
                                        "type": "number"
                                    }
                                }
                            },
                            "geoLocationPolygons": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "inPolygonPoint": {
                                            "type": "object",
                                            "properties": {
                                                "pointLatitude": {
                                                    "type": "number"
                                                },
                                                "pointLongitude": {
                                                    "type": "number"
                                                }
                                            }
                                        },
                                        "polygonPoints": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "pointLatitude": {
                                                        "type": "number"
                                                    },
                                                    "pointLongitude": {
                                                        "type": "number"
                                                    }
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                },
                "language": {
                    "type": "string"
                },
                "publicationYear": {
                    "type": "string"
                },
                "publisher": {
                    "type": "object",
                    "properties": {
                        "lang": {
                            "type": "string"
                        },
                        "name": {
                            "type": "string"
                        },
                        "publisherIdentifier": {
                            "type": "string"
                        },
                        "publisherIdentifierScheme": {
                            "type": "string"
                        },
                        "schemeURI": {
                            "type": "string"
                        }
                    }
                },
                "relatedIdentifiers": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "relatedIdentifier": {
                                "type": "string"
                            },
                            "relatedIdentifierType": {
                                "type": "string"
                            },
                            "relatedMetadataScheme": {
                                "type": "string"
                            },
                            "relationType": {
                                "type": "string"
                            },
                            "resourceTypeGeneral": {
                                "type": "string"
                            },
                            "schemeType": {
                                "type": "string"
                            },
                            "schemeURI": {
                                "type": "string"
                            }
                        }
                    }
                },
                "relatedItems": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "contributors": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "affiliation": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "affiliationIdentifier": {
                                                        "type": "string"
                                                    },
                                                    "affiliationIdentifierScheme": {
                                                        "type": "string"
                                                    },
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "schemeURI": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        },
                                        "contributorType": {
                                            "type": "string"
                                        },
                                        "familyName": {
                                            "type": "string"
                                        },
                                        "givenName": {
                                            "type": "string"
                                        },
                                        "lang": {
                                            "type": "string"
                                        },
                                        "name": {
                                            "type": "string"
                                        },
                                        "nameIdentifiers": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "nameIdentifier": {
                                                        "type": "string"
                                                    },
                                                    "nameIdentifierScheme": {
                                                        "type": "string"
                                                    },
                                                    "schemeURI": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        },
                                        "nameType": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "creators": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "affiliation": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "affiliationIdentifier": {
                                                        "type": "string"
                                                    },
                                                    "affiliationIdentifierScheme": {
                                                        "type": "string"
                                                    },
                                                    "name": {
                                                        "type": "string"
                                                    },
                                                    "schemeURI": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        },
                                        "familyName": {
                                            "type": "string"
                                        },
                                        "givenName": {
                                            "type": "string"
                                        },
                                        "lang": {
                                            "type": "string"
                                        },
                                        "name": {
                                            "type": "string"
                                        },
                                        "nameIdentifiers": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "nameIdentifier": {
                                                        "type": "string"
                                                    },
                                                    "nameIdentifierScheme": {
                                                        "type": "string"
                                                    },
                                                    "schemeURI": {
                                                        "type": "string"
                                                    }
                                                }
                                            }
                                        },
                                        "nameType": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "edition": {
                                "type": "string"
                            },
                            "firstPage": {
                                "type": "string"
                            },
                            "issue": {
                                "type": "string"
                            },
                            "lastPage": {
                                "type": "string"
                            },
                            "number": {
                                "type": "string"
                            },
                            "numberType": {
                                "type": "string"
                            },
                            "publicationYear": {
                                "type": "string"
                            },
                            "publisher": {
                                "type": "string"
                            },
                            "relatedItemIdentifier": {
                                "type": "object",
                                "properties": {
                                    "relatedItemIdentifier": {
                                        "type": "string"
                                    },
                                    "relatedItemIdentifierType": {
                                        "type": "string"
                                    }
                                }
                            },
                            "relatedItemType": {
                                "type": "string"
                            },
                            "relatedMetadataScheme": {
                                "type": "string"
                            },
                            "relationType": {
                                "type": "string"
                            },
                            "resourceTypeGeneral": {
                                "type": "string"
                            },
                            "schemeType": {
                                "type": "string"
                            },
                            "schemeURI": {
                                "type": "string"
                            },
                            "titles": {
                                "type": "array",
                                "items": {
                                    "type": "object",
                                    "properties": {
                                        "lang": {
                                            "type": "string"
                                        },
                                        "title": {
                                            "type": "string"
                                        },
                                        "titleType": {
                                            "type": "string"
                                        }
                                    }
                                }
                            },
                            "volume": {
                                "type": "string"
                            }
                        }
                    }
                },
                "resourceType": {
                    "type": "object",
                    "properties": {
                        "resourceType": {
                            "type": "string"
                        },
                        "resourceTypeGeneral": {
                            "type": "string"
                        }
                    }
                },
                "rightsList": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "lang": {
                                "type": "string"
                            },
                            "rights": {
                                "type": "string"
                            },
                            "rightsIdentifier": {
                                "type": "string"
                            },
                            "rightsIdentifierScheme": {
                                "type": "string"
                            },
                            "rightsURI": {
                                "type": "string"
                            },
                            "schemeURI": {
                                "type": "string"
                            }
                        }
                    }
                },
                "schemaVersion": {
                    "type": "string"
                },
                "sizes": {
                    "type": "array",
                    "items": {
                        "type": "string"
                    }
                },
                "subjects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "classificationCode": {
                                "type": "string"
                            },
                            "lang": {
                                "type": "string"
                            },
                            "schemeURI": {
                                "type": "string"
                            },
                            "subject": {
                                "type": "string"
                            },
                            "subjectScheme": {
                                "type": "string"
                            },
                            "valueURI": {
                                "type": "string"
                            }
                        }
                    }
                },
                "titles": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "lang": {
                                "type": "string"
                            },
                            "title": {
                                "type": "string"
                            },
                            "titleType": {
                                "type": "string"
                            }
                        }
                    }
                },
                "url": {
                    "type": "string"
                },
                "version": {
                    "type": "string"
                }
            }
        }

