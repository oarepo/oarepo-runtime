import pytest
from werkzeug.local import LocalProxy

from oarepo_runtime.cli.configuration import remove_lazy_objects

@pytest.fixture(scope="module")
def obj1():
    return {
        'a': "a1",
        'b': "b1",
        'c': LocalProxy(lambda: 'lazy'),
    }

@pytest.fixture(scope="module")
def obj2():
    return {
        'a': "a1",
        'b': {"b1"},
        'c': LocalProxy(lambda: 'lazy'),
    }


@pytest.fixture(scope="module")
def obj3():
    return {
        'a': "a1",
        'b': [1, 2, [3, 4, (5, 6)], {"key": "value"}, {LocalProxy(lambda: "lazy"), 8}],
        'c': LocalProxy(lambda: 'lazy'),
    }

@pytest.fixture(scope="module")
def obj4():
    return {
        'a': "a1",
        'b': [1, 2, [3, 4, (5, 6)], {"key": "value"}, {LocalProxy(lambda: "lazy"), 8}],
        'c': ("tuple_item1", "tuple_item2", [80, LocalProxy(lambda: 'lazy')], {"key_in_tuple": "value_in_tuple"})
    }

@pytest.fixture(scope="module")
def obj5():
    return {
        'a': "a1",
        'b': {100, 200, frozenset([300, LocalProxy(lambda: "lazy"), 80])},
        'c': ("tuple_item1", "tuple_item2", [80, LocalProxy(lambda: 'lazy')], {"key_in_tuple": "value_in_tuple"})
    }

@pytest.fixture(scope="module")
def obj6():
    return {
        'a': [1, 2, [3, 4, (5, LocalProxy(lambda: "lazy"))]],
        'b': {"100":100, "200":200, "frozenset":frozenset([300, LocalProxy(lambda: "lazy"),80])},
        'c': ("tuple_item1", "tuple_item2", [80, LocalProxy(lambda: 'lazy')], {"key_in_tuple": ["value_in_tuple", LocalProxy(lambda: "lazy")]})
    }

@pytest.fixture(scope="module")
def obj7():
    return {
        'a': [1, 2, [3, 4, LocalProxy(lambda: "lazy")]],
        'b': {"100":100, "200":200, "frozenset":frozenset([300, LocalProxy(lambda: "lazy"),80])},
        'c': ("tuple_item1", "tuple_item2", [80, LocalProxy(lambda: 'lazy')], {"key_in_tuple": ["value_in_tuple", LocalProxy(lambda: "lazy")]})
    }

def test_remove_lazy_objects(obj1, obj2, obj3, obj4, obj5, obj6, obj7):
    ret = remove_lazy_objects([])
    assert ret == []

    ret = remove_lazy_objects(())
    assert ret == ()

    ret = remove_lazy_objects("string")
    assert ret == "string"

    ret = remove_lazy_objects(1)
    assert ret == 1

    ret = remove_lazy_objects(True)
    assert ret == True

    ret = remove_lazy_objects(set())
    assert ret == set()

    assert frozenset() == remove_lazy_objects(frozenset())

    assert dict() == remove_lazy_objects({})

    ret = remove_lazy_objects(obj1)
    assert ret == {'a': "a1", "b": "b1"}

    ret = remove_lazy_objects(obj2)
    assert ret == {'a': "a1", "b": {"b1"}}

    ret = remove_lazy_objects(obj3)
    assert ret == {'a': "a1", "b": [1, 2, [3, 4, (5, 6)], {"key": "value"}, {8}]}


    ret = remove_lazy_objects(obj4)
    assert ret == {'a': "a1", "b": [1, 2, [3, 4, (5, 6)], {"key": "value"}, {8}],
                   'c': ('tuple_item1', 'tuple_item2', [80], {"key_in_tuple": "value_in_tuple"})}

    ret = remove_lazy_objects(obj5)
    assert ret == {'a': "a1", "b": {100, 200, frozenset([300, 80])},
                   'c': ('tuple_item1', 'tuple_item2', [80], {"key_in_tuple": "value_in_tuple"})}

    ret = remove_lazy_objects(obj6)
    assert ret == {
        'a': [1, 2, [3, 4, (5,)],],
        'b': {"100":100, "200":200, "frozenset":frozenset([300, 80])},
        'c': ('tuple_item1', 'tuple_item2', [80], {"key_in_tuple": ["value_in_tuple"]})
    }

    ret = remove_lazy_objects(obj7)
    assert ret == {
        'a': [1, 2, [3, 4],],
        'b': {"100":100, "200":200, "frozenset":frozenset([300, 80])},
        'c': ('tuple_item1', 'tuple_item2', [80], {"key_in_tuple": ["value_in_tuple"]})
    }


