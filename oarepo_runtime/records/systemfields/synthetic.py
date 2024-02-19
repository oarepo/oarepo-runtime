from invenio_records.systemfields import SystemField

from .mapping import MappingSystemFieldMixin


class SyntheticSystemField(MappingSystemFieldMixin, SystemField):
    """
        A class that provides a synthetic system field, that is a system field that
        generates its content from what is already present inside the record.

        The field is not stored in the record, but is generated on the fly when
        the record is being indexed.

        Usage:

        1. Create a new class that inherits from SyntheticSystemField
        2. Implement the _value method that returns the value of the field from a data (
           either a dictionary or an instance of the record class)
        3. Put the class onto the record. If you use oarepo-model-builder, add it to the model
           like:
           ```yaml
    record:
      record:
        extra-code: |-2
              # extra custom fields for facets
              faculty = {{common.theses.synthetic_fields.FacultySystemField}}()
              department = {{common.theses.synthetic_fields.DepartmentSystemField}}()
              defenseYear = {{common.theses.synthetic_fields.DefenseYearSystemField}}()
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

    def search_dump(self, data):
        dt = self._value(data)
        if dt:
            data[self.key] = dt

    def search_load(self, data):
        data.pop(self.key)

    def __get__(self, record, owner=None):
        if record is None:
            return self
        return self._value(record)

    def _value(self, data):
        raise NotImplementedError("You must implement the _value method")
