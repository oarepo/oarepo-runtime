#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test cases for the Model class resource property in oarepo_runtime.api."""

from __future__ import annotations

import logging
from typing import Any, NamedTuple

import pytest
from invenio_records import Record
from invenio_records.systemfields import MultiRelationsField
from invenio_records.systemfields.relations.errors import InvalidRelationValue
from invenio_vocabularies.records.api import Vocabulary

from oarepo_runtime.records.systemfields.relations import PIDArbitraryNestedListRelation

log = logging.getLogger(__name__)

logging.basicConfig(level=logging.INFO)


class TestRecord(Record):
    """Test record with arbitrary relations."""

    relations = MultiRelationsField(
        single_array_no_field=PIDArbitraryNestedListRelation(
            array_paths=["single_array"],
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
        single_array_with_field=PIDArbitraryNestedListRelation(
            array_paths=["with_field"],
            relation_field="fld",
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
        two_arrays_no_field=PIDArbitraryNestedListRelation(
            array_paths=["two_arrays", "no_field"],
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
        two_arrays_with_field=PIDArbitraryNestedListRelation(
            array_paths=["two_arrays", "with_field"],
            relation_field="fld",
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
        three_arrays_no_field=PIDArbitraryNestedListRelation(
            array_paths=["three_arrays", "inner_array", "no_field"],
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
        three_arrays_with_field=PIDArbitraryNestedListRelation(
            array_paths=["three_arrays", "inner_array", "with_field"],
            relation_field="fld",
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
        three_arrays_no_field_nested_path=PIDArbitraryNestedListRelation(
            array_paths=[
                "three_arrays_with_subfield.a",
                "inner_array.b",
                "no_field.c",
            ],
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
        three_arrays_with_field_nested_path=PIDArbitraryNestedListRelation(
            array_paths=[
                "three_arrays_with_subfield.b",
                "inner_array.c",
                "with_field.d",
            ],
            relation_field="fld.e",
            keys=["title"],
            pid_field=Vocabulary.pid.with_type_ctx("test-vocab"),  # type: ignore[attr-defined]
            cache_key="test-vocab",
        ),
    )


@pytest.fixture
def ok_data():
    return {
        "single_array": [{"id": "a"}, {"id": "b"}],
        "with_field": [{"fld": {"id": "a"}}, {"fld": {"id": "b"}}],
        "two_arrays": [
            {"no_field": [{"id": "a"}, {"id": "b"}]},
            {"with_field": [{"fld": {"id": "a"}}, {"fld": {"id": "b"}}]},
        ],
        "three_arrays": [
            {
                "inner_array": [
                    {
                        "no_field": [{"id": "a"}, {"id": "b"}],
                        "with_field": [
                            {"fld": {"id": "a"}},
                            {"fld": {"id": "b"}},
                        ],
                    }
                ]
            },
        ],
        "three_arrays_with_subfield": {
            "a": [{"inner_array": {"b": [{"no_field": {"c": [{"id": "a"}]}}]}}],
            "b": [{"inner_array": {"c": [{"with_field": {"d": [{"fld": {"e": {"id": "b"}}}]}}]}}],
        },
    }


@pytest.fixture
def bad_data():
    # all ids invalid
    return {
        "single_array": [{"id": "bad_id"}],
        "with_field": [{"fld": {"id": "bad_id"}}],
        "two_arrays": [
            {"no_field": [{"id": "bad_id"}]},
            {"with_field": [{"fld": {"id": "bad_id"}}]},
        ],
        "three_arrays": [
            {
                "inner_array": [
                    {
                        "no_field": [{"id": "bad_id"}],
                        "with_field": [{"fld": {"id": "bad_id"}}],
                    }
                ]
            },
        ],
        "three_arrays_with_subfield": {
            "a": [{"inner_array": {"b": [{"no_field": {"c": [{"id": "bad_id"}]}}]}}],
            "b": [{"inner_array": {"c": [{"with_field": {"d": [{"fld": {"e": {"id": "bad_id"}}}]}}]}}],
        },
    }


@pytest.fixture
def validation_data():
    class VD(NamedTuple):
        """Validation data tuple."""

        error_pos: str
        error_type: str
        wrap: bool
        exc_type: type[Exception]
        msg: str

    return [
        VD(
            "single_array",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
        VD(
            "single_array",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid structure, expecting list",
        ),
        VD(
            "with_field",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            r"Invalid value \[{'id': 'non-existing-id'}\], should not be list.",
        ),
        VD(
            "with_field",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
        VD(
            "two_arrays",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
        VD(
            "two_arrays",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid structure, expecting list",
        ),
        VD(
            "two_arrays_with_field",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            r"Invalid value \[{'id': 'non-existing-id'}\], should not be list.",
        ),
        VD(
            "two_arrays_with_field",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
        VD(
            "three_arrays",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
        VD(
            "three_arrays",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid structure, expecting list",
        ),
        VD(
            "three_arrays_with_field",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            r"Invalid value \[{'id': 'non-existing-id'}\], should not be list.",
        ),
        VD(
            "three_arrays_with_field",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
        VD(
            "three_arrays_nested",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
        VD(
            "three_arrays_nested",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid structure, expecting list",
        ),
        VD(
            "three_arrays_nested_with_field",
            "bad_id",
            True,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            r"Invalid value \[{'id': 'non-existing-id'}\], should not be list.",
        ),
        VD(
            "three_arrays_nested_with_field",
            "bad_id",
            False,  # noqa: FBT003 # boolean operator ok here
            InvalidRelationValue,
            "Invalid value non-existing-id",
        ),
    ]


def create_invalid_record(error_pos, error_type, wrap_if_error):
    def get_id(pos: int, wrap_if_ok: bool) -> Any:
        """Get id for position, possibly invalid."""

        def potentially_wrap(id_: str, wrap: bool) -> Any:
            """Wrap the id in a list if required."""
            if wrap:
                return [{"id": id_}]
            return {"id": id_}

        if pos != error_pos:
            return potentially_wrap("a", wrap_if_ok)

        match error_type:
            case "bad_id":
                return potentially_wrap("non-existing-id", wrap_if_error)

    return TestRecord(
        {
            "single_array": get_id(
                "single_array",
                True,  # noqa: FBT003 # boolean operator ok here
            ),
            "with_field": [
                {
                    "fld": get_id(
                        "with_field",
                        False,  # noqa: FBT003 # boolean operator ok here
                    )
                }
            ],
            "two_arrays": [
                {
                    "no_field": get_id(
                        "two_arrays",
                        True,  # noqa: FBT003 # boolean operator ok here
                    )
                },
                {
                    "with_field": [
                        {
                            "fld": get_id(
                                "two_arrays_with_field",
                                False,  # noqa: FBT003 # boolean operator ok here
                            )
                        }
                    ]
                },
            ],
            "three_arrays": [
                {
                    "inner_array": [
                        {
                            "no_field": get_id(
                                "three_arrays",
                                True,  # noqa: FBT003 # boolean operator ok here
                            ),
                            "with_field": [
                                {
                                    "fld": get_id(
                                        "three_arrays_with_field",
                                        False,  # noqa: FBT003 # boolean operator ok here
                                    )
                                },
                            ],
                        }
                    ]
                },
            ],
            "three_arrays_with_subfield": {
                "a": [
                    {
                        "inner_array": {
                            "b": [
                                {
                                    "no_field": {
                                        "c": get_id(
                                            "three_arrays_nested",
                                            True,  # noqa: FBT003 # boolean operator ok here
                                        )
                                    }
                                }
                            ]
                        }
                    }
                ],
                "b": [
                    {
                        "inner_array": {
                            "c": [
                                {
                                    "with_field": {
                                        "d": [
                                            {
                                                "fld": {
                                                    "e": get_id(
                                                        "three_arrays_nested_with_field",
                                                        False,  # noqa: FBT003 # boolean operator ok here
                                                    )
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ],
            },
        }
    )


def test_validate_failure(app, db, search_clear, vocab_records, validation_data):
    for error_pos, error_type, wrap, exc_type, msg in validation_data:
        log.info("Testing error at %s, type %s", error_pos, error_type)
        rec = create_invalid_record(error_pos, error_type, wrap)
        with pytest.raises(exc_type, match=msg):
            rec.relations.validate()


def test_validate_ok(app, db, search_clear, vocab_records, ok_data):
    # create a vocabulary type and an item

    rec1 = TestRecord(ok_data)
    rec1.relations.validate()


def test_dereference(app, db, search_clear, vocab_records, ok_data):
    # create a vocabulary type and an item

    rec1 = TestRecord(ok_data)
    rec1.relations.dereference()
    assert remove_version(dict(rec1)) == remove_version(
        {
            "single_array": [
                {
                    "id": "a",
                    "title": {"en": "Test A", "cs": "Test A CS"},
                },
                {
                    "id": "b",
                    "title": {"en": "Test B", "cs": "Test B CS"},
                },
            ],
            "with_field": [
                {
                    "fld": {
                        "id": "a",
                        "title": {"en": "Test A", "cs": "Test A CS"},
                    }
                },
                {
                    "fld": {
                        "id": "b",
                        "title": {"en": "Test B", "cs": "Test B CS"},
                    }
                },
            ],
            "two_arrays": [
                {
                    "no_field": [
                        {
                            "id": "a",
                            "title": {"en": "Test A", "cs": "Test A CS"},
                        },
                        {
                            "id": "b",
                            "title": {"en": "Test B", "cs": "Test B CS"},
                        },
                    ]
                },
                {
                    "with_field": [
                        {
                            "fld": {
                                "id": "a",
                                "title": {"en": "Test A", "cs": "Test A CS"},
                            }
                        },
                        {
                            "fld": {
                                "id": "b",
                                "title": {"en": "Test B", "cs": "Test B CS"},
                            }
                        },
                    ]
                },
            ],
            "three_arrays": [
                {
                    "inner_array": [
                        {
                            "no_field": [
                                {
                                    "id": "a",
                                    "title": {"en": "Test A", "cs": "Test A CS"},
                                },
                                {
                                    "id": "b",
                                    "title": {"en": "Test B", "cs": "Test B CS"},
                                },
                            ],
                            "with_field": [
                                {
                                    "fld": {
                                        "id": "a",
                                        "title": {
                                            "en": "Test A",
                                            "cs": "Test A CS",
                                        },
                                    }
                                },
                                {
                                    "fld": {
                                        "id": "b",
                                        "title": {
                                            "en": "Test B",
                                            "cs": "Test B CS",
                                        },
                                    }
                                },
                            ],
                        }
                    ]
                }
            ],
            "three_arrays_with_subfield": {
                "a": [
                    {
                        "inner_array": {
                            "b": [
                                {
                                    "no_field": {
                                        "c": [
                                            {
                                                "id": "a",
                                                "title": {
                                                    "en": "Test A",
                                                    "cs": "Test A CS",
                                                },
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ],
                "b": [
                    {
                        "inner_array": {
                            "c": [
                                {
                                    "with_field": {
                                        "d": [
                                            {
                                                "fld": {
                                                    "e": {
                                                        "id": "b",
                                                        "title": {
                                                            "en": "Test B",
                                                            "cs": "Test B CS",
                                                        },
                                                    }
                                                }
                                            }
                                        ]
                                    }
                                }
                            ]
                        }
                    }
                ],
            },
        }
    )


def remove_version(data):
    """Remove @v fields from the data for easier testing."""
    if isinstance(data, list):
        return [remove_version(item) for item in data]
    if isinstance(data, dict):
        return {key: remove_version(value) for key, value in data.items() if key != "@v"}
    return data


def test_no_array_paths():
    with pytest.raises(ValueError, match=r"array_paths are required for ArbitraryNestedListRelation."):
        PIDArbitraryNestedListRelation()
    with pytest.raises(ValueError, match=r"array_paths are required for ArbitraryNestedListRelation."):
        PIDArbitraryNestedListRelation(array_paths=[])


@pytest.mark.parametrize(
    ("fld", "value"),
    [
        ("single_array_no_field", ["a"]),
        ("single_array_with_field", [{"fld": "a"}]),
        ("two_arrays_no_field", [["a"]]),
        ("two_arrays_with_field", [[{"fld": "a"}]]),
        ("three_arrays_no_field", [[["a"]]]),
        ("three_arrays_with_field", [[[{"fld": "a"}]]]),
        ("three_arrays_no_field_nested_path", [[["a"]]]),
        ("three_arrays_with_field_nested_path", [[[{"fld": {"e": "a"}}]]]),
    ],
)
def test_set_value(app, db, search_clear, vocab_records, fld, value):
    rec1 = TestRecord({})
    setattr(rec1.relations, fld, value)
    rec1.relations.validate()
    # do it second time to check that overwrite works
    setattr(rec1.relations, fld, value)
    rec1.relations.validate()


def test_set_unknown_value(app, db, search_clear, vocab_records):
    rec1 = TestRecord({})
    with pytest.raises(
        InvalidRelationValue,
        match=r"One of the values .*non-existing-id.* is invalid",
    ):
        rec1.relations.single_array_no_field = ["non-existing-id"]


def to_ids(values):
    # go deep and extract ids
    if isinstance(values, list):
        return [to_ids(v) for v in values]
    if isinstance(values, dict):
        return values.get("id")
    return values


def test_resolve_with_call(app, db, search_clear, vocab_records, ok_data):
    rec1 = TestRecord(ok_data)
    assert to_ids(list(rec1.relations.single_array_no_field())) == ["a", "b"]
    assert to_ids(list(rec1.relations.single_array_with_field())) == ["a", "b"]
    assert to_ids(list(rec1.relations.two_arrays_no_field())) == [["a", "b"], []]
    assert to_ids(list(rec1.relations.two_arrays_with_field())) == [[], ["a", "b"]]
    assert to_ids(list(rec1.relations.three_arrays_no_field())) == [[["a", "b"]]]
    assert to_ids(list(rec1.relations.three_arrays_with_field())) == [[["a", "b"]]]
    assert to_ids(list(rec1.relations.three_arrays_no_field_nested_path())) == [[["a"]]]
    assert to_ids(list(rec1.relations.three_arrays_with_field_nested_path())) == [[["b"]]]


def test_resolve_incorrect_data_structure(app, db, search_clear, vocab_records, bad_data):
    rec1 = TestRecord(bad_data)
    assert to_ids(list(rec1.relations.single_array_no_field())) == [None]
    assert to_ids(list(rec1.relations.single_array_with_field())) == [None]
    assert to_ids(list(rec1.relations.two_arrays_no_field())) == [[None], []]
    assert to_ids(list(rec1.relations.two_arrays_with_field())) == [[], [None]]
    assert to_ids(list(rec1.relations.three_arrays_no_field())) == [[[None]]]
    assert to_ids(list(rec1.relations.three_arrays_with_field())) == [[[None]]]
    assert to_ids(list(rec1.relations.three_arrays_no_field_nested_path())) == [[[None]]]
    assert to_ids(list(rec1.relations.three_arrays_with_field_nested_path())) == [[[None]]]
