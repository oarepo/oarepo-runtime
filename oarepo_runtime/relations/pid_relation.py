from invenio_db import db

from .base import Relation, RelationResult
from .lookup import LookupResult


class PIDRelationResult(RelationResult):
    def resolve(self, id_):
        """Resolve the value using the record class."""
        # TODO: handle permissions here !!!!!!
        pid_field = self.field.pid_field.field
        cache_key = (
            pid_field._provider.pid_type
            if pid_field._provider
            else pid_field._pid_type,
            id_,
        )
        if cache_key in self.cache:
            obj = self.cache[cache_key]
            return obj

        try:
            obj = self.field.pid_field.resolve(id_)
            # We detach the related record model from the database session when
            # we add it in the cache. Otherwise, accessing the cached record
            # model, will execute a new select query after a db.session.commit.
            db.session.expunge(obj.model)
            self.cache[cache_key] = obj
            return obj
        except Exception as e:
            raise KeyError(
                f"Repository object {cache_key} has not been found or there was an exception accessing it"
            ) from e

    def _needs_update_relation_value(self, relation: LookupResult):
        # Don't dereference if already referenced.
        return "@v" not in relation.value

    def _add_version_info(self, data, relation: LookupResult, resolved_object):
        data["@v"] = f"{resolved_object.id}::{resolved_object.revision_id}"


class PIDRelation(Relation):
    result_cls = PIDRelationResult

    def __init__(self, key=None, pid_field=None, **kwargs):
        super().__init__(key=key, **kwargs)
        self.pid_field = pid_field


class MetadataRelationResult(PIDRelationResult):
    def _dereference_one(self, relation: LookupResult, keys, attrs):
        ret = super()._dereference_one(relation, keys, attrs)
        if "metadata" in ret:
            ret.update(ret.pop("metadata"))
        return ret


class MetadataPIDRelation(PIDRelation):
    result_cls = MetadataRelationResult
