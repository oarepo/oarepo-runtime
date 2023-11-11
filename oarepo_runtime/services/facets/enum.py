from .base import LabelledValuesTermsFacet


class EnumTermsFacet(LabelledValuesTermsFacet):
    # TODO: https://github.com/oarepo/oarepo-runtime/issues/43
    pass
    # def value_labels(self, values):
    # field = self._params["field"]
    # field_path = field.replace(".", "/")
    # field_enum = f"{field_path}.enum."
    # return {val: lazy_gettext(f"{field_enum}{val}") for val in values}
