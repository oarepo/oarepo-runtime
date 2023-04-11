from .base import LabelledValuesTermsFacet
from flask_babelex import lazy_gettext


class EnumTermsFacet(LabelledValuesTermsFacet):
    def value_labels(self, values):
        field = self._params["field"]
        field_path = field.replace(".", "/")
        field_enum = f"{field_path}.enum."
        return {val: lazy_gettext(f"{field_enum}{val}") for val in values}
