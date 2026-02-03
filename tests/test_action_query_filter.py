#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#
"""Test cases for action query filter."""

from __future__ import annotations

from flask_principal import Identity, RoleNeed, UserNeed
from invenio_search.engine import dsl

from oarepo_runtime.services.generators import AdministrationWithQueryFilter


def _test_internal(entity, result_filter_type, is_role=False) -> None:
    g = AdministrationWithQueryFilter()
    i = Identity(entity.id)
    if is_role:
        i.provides.add(RoleNeed(entity.id))
    else:
        i.provides.add(UserNeed(entity.id))
    filter_ = g.query_filter(identity=i)
    assert isinstance(filter_, result_filter_type)


def test_user(app, db, users, search_clear):
    _test_internal(users[0], dsl.query.MatchNone)


def test_role(app, db, roles, search_clear):
    _test_internal(roles[0], dsl.query.MatchNone, is_role=True)


def test_administrator_user(app, db, user_with_administration_rights, search_clear):
    _test_internal(user_with_administration_rights, dsl.query.MatchAll)


def test_administrator_role(app, db, role_with_administration_rights, search_clear):
    _test_internal(role_with_administration_rights, dsl.query.MatchAll, is_role=True)
