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
Please rename those RUNTIME_TEST_XXX to your constants

```yaml
  record:
    imports:
      - import: oarepo_runtime.cf.CustomFields
      - import: invenio_records_resources.records.api.Record
        alias: InvenioRecord
      - import: invenio_records_resources.records.dumpers.CustomFieldsDumperExt
    extra-code: |-2
          # extra custom fields for testing ICU sorting and suggesting
          sort = CustomFields(
              "RUNTIME_TEST_SORT_CF",
              "sort",
              clear_none=True,
              create_if_missing=True,
          )
          suggest = CustomFields(
              "RUNTIME_TEST_SUGGEST_CF",
              "suggest",
              clear_none=True,
              create_if_missing=True,
          )
  search-options:
    base-classes:
      - I18nSearchOptions
    imports:
      - import: oarepo_runtime.services.search.I18nSearchOptions
    sort-options-field: extra_sort_options
    extra-code: |-2
          SORT_CUSTOM_FIELD_NAME = "RUNTIME_TEST_SORT_CF"
          SUGGEST_CUSTOM_FIELD_NAME = "RUNTIME_TEST_SUGGEST_CF"

  record-dumper:
    extensions:
      - CustomFieldsDumperExt("RUNTIME_TEST_SORT_CF", "sort")
      - CustomFieldsDumperExt("RUNTIME_TEST_SUGGEST_CF", "suggest")
```

Then add the constants to your invenio.cfg

```python
from oarepo_runtime.cf.icu import ICUSortCF, ICUSuggestCF

RUNTIME_TEST_SORT_CF = [
   ICUSortCF(
        language = "cs",
        opensearch_language = "czech",
        source_field = "metadata.title",
        # cf_name=None,   # name of generated custom field, default is <language>
        # country=None,    
        # variant=None,
        # sort_option=None, # default is last part of <source_field>
    )
]
RUNTIME_TEST_SUGGEST_CF = [
   ICUSuggestCF(
      language="cs", 
      opensearch_language="czech", 
      source_field="metadata.title",
      # cf_name = None    # name of generated custom field, default is <language>
   )
]
```

Then run `invenio oarepo cf init` to initialize custom fields,
`invenio oarepo index reindex` if you already have data inside the repository
and from this moment on, `/records?sort=title` 