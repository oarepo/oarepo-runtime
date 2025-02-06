from oarepo_runtime.services.components import _sort_components


class FakeComponent:
    pass


def make_component(name, depends_on=None, affects=None):
    fields = {}
    if depends_on:
        fields["depends_on"] = depends_on
    if affects:
        fields["affects"] = affects
    return type(name, (FakeComponent,), fields)


def test_component_no_dependencies():
    components = [
        make_component("A"),
        make_component("B"),
        make_component("C"),
        make_component("D"),
    ]
    assert _sort_components(components) == components


def test_component_after_all():
    components = [
        make_component("A", depends_on=["*"]),
        make_component("B"),
        make_component("C"),
        make_component("D"),
    ]
    assert [x.__name__ for x in _sort_components(components)] == ["B", "C", "D", "A"]


def test_component_after_all_2():
    components = [
        make_component("A", depends_on="*"),
        make_component("B"),
        make_component("C"),
        make_component("D"),
    ]
    assert [x.__name__ for x in _sort_components(components)] == ["B", "C", "D", "A"]


def test_component_after_all_direct():
    components = [
        a := make_component("A", depends_on="*"),
        make_component("B", depends_on=[a]),
        make_component("C"),
        make_component("D"),
    ]
    assert [x.__name__ for x in _sort_components(components)] == ["C", "D", "A", "B"]


def test_component_before_all():
    components = [
        make_component("A"),
        make_component("B"),
        make_component("C"),
        make_component("D", affects=["*"]),
    ]
    assert [x.__name__ for x in _sort_components(components)] == ["D", "A", "B", "C"]


def test_component_before_all_direct():
    components = [
        make_component("A"),
        make_component("B"),
        make_component("C"),
        d := make_component("D", affects=["*"]),
        make_component("E", affects=[d]),
    ]
    assert [x.__name__ for x in _sort_components(components)] == [
        "E",
        "D",
        "A",
        "B",
        "C",
    ]


def test_component_in_between():
    a = make_component("A")
    c = make_component("C")
    b = make_component("B", affects=[a], depends_on=[c])
    components = [a, b, c]
    assert [x.__name__ for x in _sort_components(components)] == ["C", "B", "A"]
