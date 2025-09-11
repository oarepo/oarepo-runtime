#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Tests for selectors module."""

from __future__ import annotations

from oarepo_runtime.records.systemfields.selectors import PathSelector, Selector, getter


def test_getter_with_nested_dict() -> None:
    data = {"a": {"b": {"c": 1}}}
    path = ["a", "b", "c"]
    result = list(getter(data, path))
    assert result == [1]


def test_getter_with_list_inside_dict() -> None:
    data = {"a": {"b": {"c": [1, 2, 3]}}}
    path = ["a", "b", "c"]
    result = list(getter(data, path))
    assert result == [1, 2, 3]


def test_getter_with_list_of_dicts() -> None:
    data = [{"a": {"b": 1}}, {"a": {"b": 2}}, {"a": {"b": 3}}]
    path = ["a", "b"]
    result = list(getter(data, path))
    assert result == [1, 2, 3]


def test_getter_with_empty_path_on_scalar() -> None:
    data = 42
    path = []
    result = list(getter(data, path))
    assert result == [42]


def test_getter_with_empty_path_on_list() -> None:
    data = [1, 2, 3]
    path = []
    result = list(getter(data, path))
    assert result == [1, 2, 3]


def test_getter_missing_key_returns_empty() -> None:
    data = {"a": {"b": {"c": 1}}}
    path = ["x", "y"]
    result = list(getter(data, path))
    assert result == []


def test_selector() -> None:
    class MySelector(Selector):
        pass

    selector = MySelector()
    assert selector.select({}) == []


def test_path_selector() -> None:
    path_selector = PathSelector("a.b.c", "a.b.d", "x.y.z")

    data = {
        "a": {
            "b": {
                "c": 1,
                "d": [2, 3],
            },
        },
        "x": {
            "y": {
                "z": 4,
            },
        },
    }

    assert path_selector.select(data) == [1, 2, 3, 4]
