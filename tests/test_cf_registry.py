from invenio_records import Record

from oarepo_runtime.services.components import cf_registry, CustomFieldsComponent
from oarepo_runtime.services.custom_fields import InlinedCustomFields, CustomFields


def test_cf_registry(app, db):
    class TestRecord(Record):
        cf1 = CustomFields("CF1")
        cf2 = InlinedCustomFields("CF2")

    fields = cf_registry.lookup(TestRecord)
    assert {x.key for x in fields} == {"cf1", "cf2"}

    rec = TestRecord({})
    CustomFieldsComponent(None).create(None, record=rec, data={"cf1": {"a": 1}, "blah": "aa"})
    assert rec['cf1'] == {"a": 1}
    assert rec['blah'] == "aa"
