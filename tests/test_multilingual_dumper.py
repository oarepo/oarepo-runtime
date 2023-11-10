import pytest

from oarepo_runtime.records.dumpers.multilingual_dumper import MultilingualDumper
from oarepo_runtime.utils.path import PathPrefix, PathTraversal


@pytest.fixture
def traversal():
    return PathTraversal(["a/b", "a/c/e", "d"])


def test_create_tree_simple(traversal):
    traversal = PathTraversal(["a/b", "a/c/e", "d"])
    assert traversal._path_tree == PathPrefix(
        key="",
        matched_path=None,
        sub_prefixes=[
            PathPrefix(
                key="a",
                matched_path=None,
                sub_prefixes=[
                    PathPrefix(key="b", matched_path=0, sub_prefixes=[]),
                    PathPrefix(
                        key="c",
                        matched_path=None,
                        sub_prefixes=[
                            PathPrefix(key="e", matched_path=1, sub_prefixes=[])
                        ],
                    ),
                ],
            ),
            PathPrefix(key="d", matched_path=2, sub_prefixes=[]),
        ],
    )


def add_one(traversal, data):
    for path in traversal.iter(data):
        path[-1].set(path[-1].current + 1)
    return data


def test_load_none(traversal):
    assert add_one(traversal, {}) == {}


def test_load_one(traversal):
    assert add_one(traversal, {"a": {"b": 1}}) == {"a": {"b": 2}}


def test_load_bad_type(traversal):
    assert add_one(traversal, {"a": 1}) == {"a": 1}


def test_load_all(traversal):
    assert add_one(traversal, {"a": {"b": 1, "c": {"e": 2}}, "d": 3}) == {
        "a": {"b": 2, "c": {"e": 3}},
        "d": 4,
    }


def test_load_array(traversal):
    assert add_one(traversal, {"a": {"b": [1, 2, 3]}}) == {"a": {"b": [2, 3, 4]}}


def test_load_node_array(traversal):
    assert add_one(
        traversal,
        {"a": [{"b": 1}, {"b": 2}]},
    ) == {"a": [{"b": 2}, {"b": 3}]}


class TestDumper(MultilingualDumper):
    paths = ["a/b"]
    SUPPORTED_LANGS = ["en", "cs"]


def test_i18n_dumper_no_empty():
    dumper = TestDumper()
    assert dumper.dump(None, {}) == {}


def test_i18n_dumper_single():
    dumper = TestDumper()
    assert dumper.dump(None, {"a": {"b": {"lang": "en", "value": "test"}}}) == {
        "a": {"b": {"lang": "en", "value": "test"}, "b_en": ["test"]}
    }


def test_i18n_dumper_both():
    dumper = TestDumper()
    assert dumper.dump(
        None,
        {
            "a": {
                "b": [
                    {"lang": "en", "value": "test"},
                    {"lang": "cs", "value": "pokus"},
                ]
            }
        },
    ) == {
        "a": {
            "b": [{"lang": "en", "value": "test"}, {"lang": "cs", "value": "pokus"}],
            "b_en": ["test"],
            "b_cs": ["pokus"],
        }
    }


def test_i18n_dumper_in_array():
    dumper = TestDumper()
    assert dumper.dump(
        None,
        {
            "a": [
                {
                    "b": [
                        {"lang": "en", "value": "test"},
                        {"lang": "cs", "value": "pokus"},
                    ]
                }
            ]
        },
    ) == {
        "a": [
            {
                "b": [
                    {"lang": "en", "value": "test"},
                    {"lang": "cs", "value": "pokus"},
                ],
                "b_cs": ["pokus"],
                "b_en": ["test"],
            }
        ]
    }


def test_i18n_dumper_array_values():
    dumper = TestDumper()
    assert set(
        dumper.dump(
            None,
            {
                "a": {
                    "b": [
                        {"lang": "en", "value": "test"},
                        {"lang": "en", "value": "test1"},
                    ]
                }
            },
        )["a"]["b_en"]
    ) == {"test1", "test"}


def test_i18n_loader_no_empty():
    dumper = TestDumper()
    assert dumper.load({}, None) == {}


def test_i18n_loader_single():
    dumper = TestDumper()
    assert dumper.load(
        {"a": {"b": {"lang": "en", "value": "test"}, "b_en": ["test"]}}, None
    ) == {"a": {"b": {"lang": "en", "value": "test"}}}


def test_i18n_loader_both():
    dumper = TestDumper()
    assert dumper.load(
        {
            "a": {
                "b": [
                    {"lang": "en", "value": "test"},
                    {"lang": "cs", "value": "pokus"},
                ],
                "b_en": ["test"],
                "b_cs": ["pokus"],
            }
        },
        None,
    ) == {
        "a": {
            "b": [
                {"lang": "en", "value": "test"},
                {"lang": "cs", "value": "pokus"},
            ]
        }
    }


def test_i18n_dumper_in_array():
    dumper = TestDumper()
    assert dumper.load(
        {
            "a": [
                {
                    "b": [
                        {"lang": "en", "value": "test"},
                        {"lang": "cs", "value": "pokus"},
                    ],
                    "b_cs": ["pokus"],
                    "b_en": ["test"],
                }
            ]
        },
        None,
    ) == {
        "a": [
            {
                "b": [
                    {"lang": "en", "value": "test"},
                    {"lang": "cs", "value": "pokus"},
                ]
            }
        ]
    }
