#
# Copyright (c) 2025 CESNET z.s.p.o.
#
# This file is a part of oarepo-runtime (see http://github.com/oarepo/oarepo-runtime).
#
# oarepo-runtime is free software; you can redistribute it and/or modify it
# under the terms of the MIT License; see LICENSE file for more details.
#

"""Tests for the ComponentData class, partially AI generated."""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING, cast

import pytest
from invenio_records_resources.services.records.components import ServiceComponent

from oarepo_runtime.services.config.components import ComponentData

if TYPE_CHECKING:
    from invenio_records_resources.services.records.service import RecordService


# Importable dummy component for obj_or_import_string tests
class ImportableComp(ServiceComponent):
    """Trivial component used for import-string resolution tests."""


mock_service = cast("RecordService", object())  # Mock service object for testing


def test_component_data_from_class_ok():
    class A(ServiceComponent):
        pass

    cd = ComponentData(A, service=mock_service)

    assert cd.original_component is A
    assert cd.component_class is A
    # MRO contains the class and its bases/mixins, but not ServiceComponent
    assert A in cd.component_mro
    assert ServiceComponent not in cd.component_mro


def test_component_data_from_invalid_class_raises():
    class NotAComponent:
        pass

    with pytest.raises(TypeError):
        ComponentData(NotAComponent, service=mock_service)


def test_component_data_from_partial_uses_underlying_class():
    class B(ServiceComponent):
        pass

    cd = ComponentData(partial(B), service=mock_service)
    assert cd.component_class is B


def test_component_data_from_function_uses_underlying_class():
    class B(ServiceComponent):
        pass

    cd = ComponentData(lambda svc: B(svc), service=mock_service)
    assert cd.component_class is B


def test_affects_all_and_depends_on_all_flags_and_conflict():
    class A(ServiceComponent):
        affects = ("*",)

    cd_a = ComponentData(A, service=mock_service)
    assert cd_a.affects_all is True
    assert cd_a.depends_on_all is False

    class B(ServiceComponent):
        depends_on = ("*",)

    cd_b = ComponentData(B, service=mock_service)
    assert cd_b.depends_on_all is True
    assert cd_b.affects_all is False

    class C(ServiceComponent):
        affects = ("*",)
        depends_on = ("*",)

    with pytest.raises(ValueError, match="cannot affect and depend on all components"):
        ComponentData(C, service=mock_service)


def test_convert_to_classes_noop():
    class Base(ServiceComponent):
        pass

    class Child(Base):
        pass

    class Uses(ServiceComponent):
        affects = (Base, Child)
        depends_on = (Base,)

    cd = ComponentData(Uses, service=mock_service)
    assert cd.affects == {Base, Child}
    assert cd.depends_on == {Base}


def test_convert_to_classes_with_strings_and_star_ignored():
    class UsesStr(ServiceComponent):
        affects: tuple[str, ...] = ()
        depends_on: tuple[str, ...] = ()

    # Assign after class creation to use the current module path
    UsesStr.affects = (
        "*",
        f"{__name__}.ImportableComp",
    )
    UsesStr.depends_on = (f"{__name__}.ImportableComp",)

    cd = ComponentData(UsesStr, service=mock_service)
    assert cd.affects_all is True  # due to "*"
    assert ImportableComp in cd.affects
    assert cd.depends_on == {ImportableComp}


def test_hash_and_equality_based_on_original_component():
    class A(ServiceComponent):
        pass

    cd1 = ComponentData(A, service=mock_service)
    cd2 = ComponentData(A, service=mock_service)
    assert cd1 == cd2
    assert hash(cd1) == hash(cd2)

    # Different partial objects are equal as well
    cd3 = ComponentData(partial(A), service=mock_service)
    cd4 = ComponentData(partial(A), service=mock_service)
    assert cd3 == cd4


def test_component_mro_contains_bases_but_not_servicecomponent():
    class Base(ServiceComponent):
        pass

    class Derived(Base):
        pass

    cd = ComponentData(Derived, service=mock_service)
    assert Derived in cd.component_mro
    assert Base in cd.component_mro
    assert ServiceComponent not in cd.component_mro


def test_convert_to_classes_rejects_non_service_component():
    class NotComponent:
        pass

    class UsesBad(ServiceComponent):
        affects = (NotComponent,)

    with pytest.raises(TypeError):
        ComponentData(UsesBad, service=mock_service)


def test_component_data_from_factory_callable():
    def factory(service: object) -> ServiceComponent:
        class Local(ServiceComponent):
            pass

        return Local(service)

    cd = ComponentData(factory, service=mock_service)
    assert issubclass(cd.component_class, ServiceComponent)
