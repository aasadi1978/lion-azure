from flask import has_request_context
from flask_login import current_user
from sqlalchemy.orm import Query as BaseQuery
from sqlalchemy import or_


class AutoScopedQuery(BaseQuery):
    """Automatically applies scoping rules based on model-level read/write definitions."""

    _user_field_map = {
        "scn_id": "scn_id",
        "group_name": "group_name",
        "user_id": "id",
    }

    def _apply_scope(self, write_op: bool = False):
        """Apply hierarchical access rules depending on whether it's a read or write operation."""

        if not has_request_context():
            return self

        if not getattr(current_user, "is_authenticated", False) or getattr(current_user, "is_admin", False):
            return self
        
        entity = self._only_full_mapper_zero("apply_scope").class_

        # Choose hierarchy based on op type
        if write_op:
            hierarchy = getattr(entity, "__scope_write__", None)
        else:
            hierarchy = getattr(entity, "__scope_read__", None)

        # Fallbacks
        if not hierarchy:
            hierarchy = getattr(entity, "__scope_hierarchy__", ["scn_id", "group_name", "user_id"])

        filters = []
        for scope_field in hierarchy:
            user_field = self._user_field_map.get(scope_field)
            if hasattr(entity, scope_field) and hasattr(current_user, user_field):
                user_value = getattr(current_user, user_field)
                if user_value is not None:
                    filters.append(getattr(entity, scope_field) == user_value)

        if not filters:
            return self

        # Combine logic: broader for reads, stricter for writes
        condition = or_(*filters) if not write_op else filters[0]
        return self.enable_assertions(False).filter(condition)

    # --- Scoped CRUD operations ---
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs)._apply_scope()

    def filter_by(self, **kwargs):
        return super().filter_by(**kwargs)._apply_scope()

    def update(self, values, synchronize_session='evaluate'):
        # write operation → scn_id level typically
        return self._apply_scope(write_op=True).update(values, synchronize_session=synchronize_session)

    def delete(self, synchronize_session='evaluate'):
        # write operation → scn_id level typically
        return self._apply_scope(write_op=True).delete(synchronize_session=synchronize_session)

    def __iter__(self):
        return super(AutoScopedQuery, self._apply_scope()).__iter__()

    def all(self):
        return self._apply_scope().all()

    def first(self):
        return self._apply_scope().first()

    def count(self):
        return self._apply_scope().count()

    def get(self, ident):
        q = self._apply_scope().filter_by(id=ident)
        return q.first()
