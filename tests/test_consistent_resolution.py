import itertools

from oarepo_runtime.services.schema import consistent_resolution


class A:
    pass


class B(A):
    pass


class C(A):
    pass


class D(B, C):
    pass


def test_consistent_resolution():
    try:
        type("Test", (A, B), {})
        raise AssertionError(
            "Should not be able to create a class with inconsistent MRO"
        )
    except TypeError:
        pass  # sanity check passed
    for clz in (A, B, C, D):
        consistent_resolution(clz)

    for clz in itertools.product((A, B, C, D), repeat=2):
        consistent_resolution(clz[0], clz[1])

    for clz in itertools.product((A, B, C, D), repeat=3):
        consistent_resolution(clz[0], clz[1], clz[2])

    for clz in itertools.product((A, B, C, D), repeat=4):
        consistent_resolution(clz[0], clz[1], clz[2], clz[3])
