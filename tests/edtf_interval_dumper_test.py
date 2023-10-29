from oarepo_runtime.records.dumpers.edtf_interval import EDTFIntervalDumperExt


class TestDumperExt(EDTFIntervalDumperExt):
    paths = ["a", "b/a"]


def test_edtf_interval_dump():
    dumper = TestDumperExt()
    assert dumper.dump({}, {"a": "1970/1990"}) == {"a": {"gte": "1970", "lte": "1990"}}

    assert dumper.dump({}, {"b": {"a": "1970/1990"}}) == {
        "b": {"a": {"gte": "1970", "lte": "1990"}}
    }

    assert dumper.dump({}, {"a": "1970/"}) == {"a": {"gte": "1970"}}
    assert dumper.dump({}, {"a": "/1970"}) == {"a": {"lte": "1970"}}


def test_edtf_interval_load():
    dumper = TestDumperExt()
    assert dumper.load({"a": {"gte": "1970", "lte": "1990"}}, None) == {
        "a": "1970/1990"
    }

    assert dumper.load({"b": {"a": {"gte": "1970", "lte": "1990"}}}, None) == {
        "b": {"a": "1970/1990"}
    }

    assert dumper.load({"a": {"gte": "1970"}}, None) == {"a": "1970/"}
    assert dumper.load({"a": {"lte": "1970"}}, None) == {"a": "/1970"}
