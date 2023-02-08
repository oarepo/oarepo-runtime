from invenio_records_resources.records.systemfields.relations import (
    PIDRelation,
    PIDListRelation,
    PIDNestedListRelation,
)
from invenio_records.systemfields.relations import (
    RelationResult,
    RelationListResult,
    RelationNestedListResult,
)
from invenio_records.dictutils import dict_lookup, dict_set


class MetadataRelationResultMixin:
    def _dereference_one(self, data, keys, attrs):
        ret = super()._dereference_one(data, keys, attrs)
        if "metadata" in ret:
            ret.update(ret.pop("metadata"))
        return ret


class MetadataRelationResult(MetadataRelationResultMixin, RelationResult):
    pass


class MetadataRelationListResult(MetadataRelationResultMixin, RelationListResult):
    pass


class MetadataRelationNestedListResult(
    MetadataRelationResultMixin, RelationNestedListResult
):
    pass


class MetadataPIDRelation(PIDRelation):
    result_cls = MetadataRelationResult


class MetadataPIDListRelation(PIDListRelation):
    result_cls = MetadataRelationListResult


class MetadataPIDNestedListRelation(PIDNestedListRelation):
    result_cls = MetadataRelationNestedListResult
