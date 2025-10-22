# lion/orm_azure/scoped_query.py
from sqlalchemy.orm import Query as BaseQuery
from flask_login import current_user


class GroupScopedQuery(BaseQuery):
    """Automatically filters by current user's group_name if authenticated."""
    def _apply_scope(self):
        if not current_user.is_authenticated:
            return self
        entity = self._only_full_mapper_zero("apply_scope").class_
        if hasattr(entity, "group_name"):
            return self.filter(entity.group_name == current_user.group_name)
        return self

    # Apply scope transparently when the query is iterated or executed
    def __iter__(self):
        return super(GroupScopedQuery, self._apply_scope()).__iter__()

    def all(self):
        return self._apply_scope().all()

    def first(self):
        return self._apply_scope().first()

    def count(self):
        return self._apply_scope().count()

    def get(self, ident):
        # Optionally restrict .get() lookups by scope too
        q = self._apply_scope().filter_by(id=ident)
        return q.first()


class UserScopedQuery(BaseQuery):
    """Automatically filters by current user's user_id if authenticated."""
    def _apply_scope(self):
        if not current_user.is_authenticated:
            return self
        entity = self._only_full_mapper_zero("apply_scope").class_
        if hasattr(entity, "user_id"):
            return self.filter(entity.user_id == current_user.id)
        return self

    def __iter__(self):
        return super(UserScopedQuery, self._apply_scope()).__iter__()

    def all(self):
        return self._apply_scope().all()

    def first(self):
        return self._apply_scope().first()

    def count(self):
        return self._apply_scope().count()

    def get(self, ident):
        q = self._apply_scope().filter_by(id=ident)
        return q.first()
