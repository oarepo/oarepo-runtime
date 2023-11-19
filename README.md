# OARepo runtime

The base of `invenio oarepo` client and a set of classes/functions that help with code-generated features:

## Custom fields

Provides support for custom fields identification and iteration and `invenio oarepo cf init` 
initialization tool for customfields.

## Expansions

Provides expandable field implementation and service mixin for referenced record (in case you do not want to use relations).

## Facets

An implementation of nested labeled facet.

## i18n

Validator for language codes.

## Relations

Replacement of Invenio relations. Fixes the following issues:

1. Invenio relations can occur only on specific paths and for each pattern, different class must be used
   (Relation, ListRelation, NestedListRelation)
2. PID Cache is isolated per request, not set directly on field
3. Allows to map keys - A key from related object can be renamed/remapped to a different key/path
4. Provides classes to reference parts of the same record

```yaml
# article, id 12
metadata:
    title: blah
```

with mapping referenced article would look like (mapping: `{key: 'metadata.title', target: 'title'}`):

```yaml
# dataset:
metadata:
    articles:
    - id: 12
      @v: 1
      title: blah
```

With Invenio PID relation, it would be:

```yaml
# dataset:
metadata:
    articles:
    - id: 12
      "@v": 1
      metadata:
        title: blah
```

## Validation

This module provides a marshmallow validator for date strings.

## Config

Provides interface and definitions for loading 
preconfigured permission sets to service config.

## ICU sort and suggestions

To use ICU sort and suggestion custom fields, provide the following configuration
to `oarepo-model-builder` (or put this stuff to your custom superclasses).

```yaml
  record:
    imports:
      - import: invenio_records_resources.records.api.Record
        alias: InvenioRecord
      - import: oarepo_runtime.records.SystemFieldDumperExt
      - import: oarepo_runtime.records.icu.ICUSortField
      - import: oarepo_runtime.records.icu.ICUSuggestField
    extra-code: |-2
          # extra custom fields for testing ICU sorting and suggesting
          sort = ICUSortField(source_field="metadata.title")
          suggest = ICUSuggestField(source_field="metadata.title")
  search-options:
    base-classes:
      - I18nSearchOptions
    imports:
      - import: oarepo_runtime.services.icu.I18nSearchOptions
      - import: oarepo_runtime.services.icu.ICUSuggestParser
      - import: oarepo_runtime.services.icu.ICUSortOptions
    sort-options-field: extra_sort_options
    extra-code: |-2
          suggest_parser_cls = ICUSuggestParser("records2")
          sort_options = ICUSortOptions("records2")

  record-dumper:
    extensions:
      - SystemFieldDumperExt()
```

Run `invenio oarepo cf init` to initialize custom fields,
`invenio oarepo index reindex` if you already have data 
inside the repository and from this moment on, 
`/records?sort=title` and `/records?suggest=abc` should work

# Command-line utils

## `invenio oarepo version`

Prints a json with versions of all installed packages. Format:

```json
{
   "package_name": "package_version",
   "package_name2": "package_version2",
   ...
}
```

## `invenio oarepo check`

Checks the repository if it has access to all infrastructure components
and that they have been initialized correctly.

Call as `invenio oarepo check -` or `invenio oarepo check <output-file>`.
Will print/write to file a json with the following format:

```json5
{
  "db": "ok|connection_error|not_initialized|migration_pending",
  "opensearch": "ok|connection_error|index_missing:<index_name>",
  "files": "ok|db_connection_error|default_location_missing|bucket_does_not_exist:<bucket_name>|db_error",
  "mq": "ok|connection_error|mq_error",
  "cache": "ok|connection_error|cache_error|cache_exception", 
  "configuration": {
     // contains the configuration from the flask app
     "key": "value",
     "key2": "value2",
     ...
  }
}
```
```json

```