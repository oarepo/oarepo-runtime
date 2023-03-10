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