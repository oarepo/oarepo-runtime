def test_testmo_integration(record_property):
    record_property("author", "mirekys")
    record_property("text:description", "This test case evaluates integration features of Testmo")
    record_property("url:github", "https://github.com/oarepo/oarepo-runtime/tests/test_testmo_integration.py")
  
    # Testmo also supports automation steps, including statuses & sub fields
    record_property("step[passed]", "Check if sky is blue")
    assert True

    record_property("step[failed]", "Check if cows are purple")
    assert False
