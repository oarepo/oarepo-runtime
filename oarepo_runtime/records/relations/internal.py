from invenio_records.systemfields.relations import InvalidRelationValue

from .base import Relation, RelationResult
from .lookup import LookupResult, lookup_key


class InternalResult(RelationResult):
    def resolve(self, id_):
        related_part = self.field.related_part

        if not related_part:
            return self.record

        potential_values = list(lookup_key(self.record, related_part))

        if not id_:
            if len(potential_values) > 1:
                raise InvalidRelationValue(
                    "Relation returned more than one part at "
                    f"{related_part} but has no id to check those parts against"
                )
            return potential_values[0].value

        for rel in potential_values:
            if not isinstance(rel.value, dict):
                raise KeyError(
                    f"Related part {related_part} does not point to an array of objects at path "
                    f"{rel.path}- array member is {type(rel.value)}: {rel.value}"
                )

            if id_ == rel.value.get("id", None):
                return rel.value

        raise KeyError(f"No data for relation at path {related_part} with id {id_}")

    def _lookup_id(self, relation: LookupResult):
        relation_id = relation.value.get("id", None)
        return relation_id


class InternalRelation(Relation):
    result_cls = InternalResult

    def __init__(self, key=None, related_part=None, **kwargs):
        super().__init__(key=key, **kwargs)
        self.related_part = related_part
