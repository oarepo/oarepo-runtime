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

Support for PID relations that remove the "metadata" element when they are referenced. So for example:

```yaml
# article, id 12
metadata:
    title: blah
```

with this class a referencing dataset would like:

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