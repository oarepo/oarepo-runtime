# Bug: `record_dict_to_linkset` crashes with HTTP 500 for record types without a DataCite export

## Summary

`oarepo_ui`'s `response_header_signposting` decorator calls `record_dict_to_linkset`, which calls
`get_export_from_serialized_record(..., export_mimetype="application/vnd.datacite.datacite+json")`.
For record types that have no DataCite export configured, `get_export_from_serialized_record` raises
`ValueError`, which propagates through `record_dict_to_linkset` and causes an HTTP 500 on every
request to that record's detail page.

The decorator already guards against a falsy linkset result (`if record_linkset:`), so the correct
silent fallback is to return an empty string (or `{}` for the JSON variant) rather than letting the
exception propagate.

## Affected version

`oarepo-runtime` 2.0.0dev59

## Steps to reproduce

1. Register a record type (e.g., `research_activity`, `sample`, `tool`) that does **not** declare
   a DataCite JSON export in its serializers configuration.
2. Create a record of that type.
3. Navigate to the record detail page.

**Result:**
```
ValueError: No export found for mimetype application/vnd.datacite.datacite+json
```
propagated from `oarepo_runtime.ext.OARepoRuntime.get_export_from_serialized_record`
through `record_dict_to_linkset`, returning HTTP 500.

## Root cause

`record_dict_to_linkset` (and `record_dict_to_json_linkset`) calls
`current_runtime.get_export_from_serialized_record` without guarding against the documented
`ValueError` that is raised when the requested export mimetype is not registered for the record
type. The call is outside the `try/except` block added in the earlier `create_linkset` fix.

```python
# Before fix — ValueError propagates
def record_dict_to_linkset(record_dict, include_reverse_relations=True):
    datacite_dict = current_runtime.get_export_from_serialized_record(
        record_dict=record_dict,
        representation=ExportRepresentation.DICTIONARY,
        export_mimetype="application/vnd.datacite.datacite+json",
    )
    return create_linkset(datacite_dict, record_dict, include_reverse_relations)
```

## Proposed fix

Wrap the `get_export_from_serialized_record` call in both `record_dict_to_linkset` and
`record_dict_to_json_linkset` with a `try/except (ValueError, KeyError)` that returns the
appropriate empty value so signposting is silently skipped for unsupported record types.

```python
# After fix
def record_dict_to_linkset(record_dict, include_reverse_relations=True):
    try:
        datacite_dict = current_runtime.get_export_from_serialized_record(
            record_dict=record_dict,
            representation=ExportRepresentation.DICTIONARY,
            export_mimetype="application/vnd.datacite.datacite+json",
        )
    except (ValueError, KeyError):
        return ""
    return create_linkset(datacite_dict, record_dict, include_reverse_relations)
```

The same pattern applies to `record_dict_to_json_linkset`, returning `{}` on error.

## Workaround (applied in frozen_testing)

`patches.py` monkey-patches both `oarepo_runtime.resources.signposting.record_dict_to_linkset`
and (if already imported) `oarepo_ui.resources.decorators.signposting.record_dict_to_linkset`
with a safe wrapper that catches `ValueError` and `KeyError`.

## Note on related upstream fix

Commit `cdd4b44` (`fix: return empty linkset during signposting error`) added a `try/except` block
inside `create_linkset`, but this does not protect against the `ValueError` raised by
`get_export_from_serialized_record` before `create_linkset` is ever called. Both fixes are needed.
