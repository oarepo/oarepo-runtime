from invenio_records.systemfields import SystemField

from .mapping import MappingSystemFieldMixin

import logging

log = logging.getLogger(__name__)


class SyntheticSystemField(MappingSystemFieldMixin, SystemField):
    """
        A class that provides a synthetic system field, that is a system field that
        generates its content from what is already present inside the record.

        The field is not stored in the record, but is generated on the fly when
        the record is being indexed.

        Usage:
        1. Check if any of the provided selectors (oarepo_runtime.records.systemfields.selectors)
           are usable for your use case. If not, create a subclass of Selector class.
        2. Put this class onto the record. If you use oarepo-model-builder, add it to the model
           like:
           ```yaml
    record:
      record:
        imports:
          - oarepo_runtime.records.systemfields.SyntheticSystemField
          - oarepo_vocabularies.records.selectors.LevelSelector
        fields:
          faculty = SyntheticSystemField(selector=LevelSelector("metadata.thesis.degreeGrantors", level=1))
          department = SyntheticSystemField(selector=LevelSelector("metadata.thesis.degreeGrantors", level=2))
          defenseYear = |
            SyntheticSystemField(selector=PathSelector("metadata.thesis.dateDefended"),
                transformer=lambda x: x[:4]
            )
           ```

        4. Add the extra fields to the mapping and facets. If using oarepo-model-builder, add it to the
           model like the following piece of code and compile the model:
           ```yaml
    record:
      properties:
        faculty:
          type: vocabulary
          vocabulary-type: institutions
          facets:
            facet-groups:
            - default
          label.cs: Fakulta
          label.en: Faculty


        department:
          type: vocabulary
          vocabulary-type: institutions
          facets:
            facet-groups:
            - default
          label.cs: Ústav
          label.en: Department

        defenseYear:
          type: integer
          facets:
            facet-groups:
            - default
          label.cs: Rok obhajoby
          label.en: Defense year
           ```
    """

    def __init__(self, selector=None, filter=None, map=None, key=None, **kwargs):
        self.selector = selector
        self.map = map
        self.filter = filter
        super().__init__(key=key, **kwargs)

    def search_dump(self, data, record):
        dt = self._value(data)
        if dt:
            key = self.key.split(".")
            d = data
            for k in key[:-1]:
                d = d.setdefault(k, {})
            d[key[-1]] = dt

    def search_load(self, data, record_cls):
        def remove_key(d, key):
            if len(key) == 1:
                d.pop(key[0], None)
            else:
                if not isinstance(d, dict) or key[0] not in d:
                    return
                remove_key(d[key[0]], key[1:])
                if not d[key[0]]:
                    d.pop(key[0])

        remove_key(data, self.key.split("."))

    def __get__(self, record, owner=None):
        if record is None:
            return self
        return self._value(record)

    def _value(self, data):
        if self.selector:
            try:
                value = list(self.selector.select(data) or [])
                value = [x for x in value if x is not None]
                if self.filter:
                    value = [x for x in value if self.filter(x)]
                if self.map:
                    ret = []
                    for x in value:
                        mapped = self.map(x)
                        if isinstance(mapped, list):
                            ret.extend(mapped)
                        elif mapped is not None:
                            ret.append(mapped)
                    value = ret
                return value
            except:
                log.exception(f"Error in selector {self.selector} for {self.key}")
                return []
        raise ValueError(
            "Please either provide a selector or subclass this class and implement a _value method"
        )
