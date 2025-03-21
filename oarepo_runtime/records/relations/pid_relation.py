from invenio_db import db

from oarepo_runtime.services.relations.errors import InvalidRelationError
from sqlalchemy.exc import NoResultFound

from .base import Relation, RelationResult, UnstrictRelationResult
from .lookup import LookupResult

class PIDRelationResult(RelationResult):
    def resolve(self, id_, data = None):
        """Resolve the value using the record class."""
        # TODO: handle permissions here !!!!!!
        try:
            pid_field_context = self.field.pid_field
            try:
                pid_type = getattr(pid_field_context, "pid_type", None)
            except:
                pass

            if pid_type is None:
                pid_field = pid_field_context.field
                if pid_field._provider:
                    if hasattr(pid_field._provider, "pid_type"):
                        pid_type = pid_field._provider.pid_type
                    else:
                        pid_type = self.field.pid_field.record_cls.__name__
                else:
                    if hasattr(pid_field, "_pid_type"):
                        pid_type = pid_field._pid_type
                    else:
                        pid_type = self.field.pid_field.record_cls.__name__
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
            if hasattr(obj, "relations") and obj.relations and hasattr(obj.relations, "dereference"):
                obj.relations.dereference()
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

class UnstrictPIDRelationResult(PIDRelationResult, UnstrictRelationResult):

    def resolve(self, id_, data):
        try:
            return super().resolve(id_, data)
        except InvalidRelationError as e:
            if isinstance(e.__cause__, NoResultFound):
                return data
            raise

class PIDRelation(Relation):
    result_cls = PIDRelationResult

    def __init__(self, key=None, pid_field=None, **kwargs):
        super().__init__(key=key, **kwargs)
        self.pid_field = pid_field

class UnstrictPIDRelation(Relation):
    result_cls = UnstrictPIDRelationResult

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
