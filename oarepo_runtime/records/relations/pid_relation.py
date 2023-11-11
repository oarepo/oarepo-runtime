from invenio_db import db

from oarepo_runtime.services.relations.errors import InvalidRelationError

from .base import Relation, RelationResult
from .lookup import LookupResult


class PIDRelationResult(RelationResult):
    def resolve(self, id_):
        """Resolve the value using the record class."""
        # TODO: handle permissions here !!!!!!
        try:
            pid_field_context = self.field.pid_field
            if hasattr(pid_field_context, "pid_type"):
                pid_type = pid_field_context.pid_type
            else:
                pid_field = pid_field_context.field
                pid_type = (
                    pid_field._provider.pid_type
                    if pid_field._provider
                    else pid_field._pid_type
                )
        except Exception as e:
            raise InvalidRelationError(
                f"PID type for field {self.field.key} has not been found or there was an exception accessing it.",
                related_id=id_,
                location=self.field.key,
            ) from e

        cache_key = (pid_type, id_)
        if cache_key in self.cache:
            obj = self.cache[cache_key]
            return obj

        try:
            obj = pid_field_context.resolve(id_)
            # We detach the related record model from the database session when
            # we add it in the cache. Otherwise, accessing the cached record
            # model, will execute a new select query after a db.session.commit.
            db.session.expunge(obj.model)
            self.cache[cache_key] = obj
            return obj
        except Exception as e:
            raise InvalidRelationError(
                f"Repository object {cache_key} has not been found or there was an exception accessing it. "
                f"Referenced from {self.field.key}.",
                related_id=id_,
                location=self.field.key,
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
    def _dereference_one(self, relation: LookupResult):
        ret = super()._dereference_one(relation)
        if "metadata" in ret:
            ret.update(ret.pop("metadata"))
        return ret


class MetadataPIDRelation(PIDRelation):
    result_cls = MetadataRelationResult
