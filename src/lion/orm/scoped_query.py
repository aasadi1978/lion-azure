from sqlalchemy.orm import Query as BaseQuery
from flask import has_request_context, session, g
from flask_login import current_user
from sqlalchemy import and_

from lion.logger.exception_logger import log_exception

class AutoScopedQuery(BaseQuery):
    """
    Automatically applies hierarchical access control based on __scope_hierarchy__.
    Supports scn_id, group_name, and user_id scopes, with model-level priority.
    """

    _user_field_map = {
        "scn_id": "scn_id",
        "group_name": "group_name",
        "user_id": "user_id",
    }

    def _get_scn_id(self):
        try:
            self._scn_id = int(getattr(g, "scn_id", None)) or int(session.get("active_scn_id", 0))
            self._group_name = getattr(g, "group_name", None) or session.get("active_group_name", 0)

        except Exception:
            log_exception(popup=False, remarks="Failed to retrieve scn_id or group_name from session or g.")
            self._scn_id = None
            self._group_name = None

    def _apply_scope(self):

        if not has_request_context():
            return self

        if not getattr(current_user, "is_authenticated", False):
            return self

        entity = self._only_full_mapper_zero("apply_scope").class_

        # get model-specific hierarchy or fallback to default
        hierarchy = getattr(entity, "__scope_hierarchy__", ["group_name"])
        self._get_scn_id()

        filters = []

        for scope_field in hierarchy:
            if not hasattr(entity, scope_field):
                continue

            user_field = self._user_field_map.get(scope_field)
            if not hasattr(current_user, user_field):
                continue

            user_value = getattr(current_user, user_field)
            if user_value is not None:
                filters.append(getattr(entity, scope_field) == user_value)

        if self._scn_id is not None:
            filters.append(getattr(entity, "scn_id") == self._scn_id)

        if self._group_name is not None:
            filters.append(getattr(entity, "group_name") == self._group_name)

        # Apply logic based on declared hierarchy
        if not filters:
            return self

        # Combine according to hierarchy: the higher-level scopes are applied first
        # (e.g., SCN → GROUP → USER), meaning broader access first, narrower next.
        condition = and_(*filters)
        return self.enable_assertions(False).filter(condition)

    # --- Same helper overrides ---
    def filter(self, *args, **kwargs):
        return super().filter(*args, **kwargs)._apply_scope()

    def filter_by(self, **kwargs):
        return super().filter_by(**kwargs)._apply_scope()

    def update(self, values, synchronize_session='evaluate'):
        return BaseQuery.update(self._apply_scope(), values, synchronize_session=synchronize_session)
        # return self._apply_scope().update(values, synchronize_session=synchronize_session)

    def delete(self, synchronize_session='evaluate'):
        return BaseQuery.delete(self._apply_scope(), synchronize_session=synchronize_session)

    def __iter__(self):
        return super(AutoScopedQuery, self)._apply_scope().__iter__()

    def all(self):
        # Apply scope, then call BaseQuery.all() directly (avoid recursion)
        scoped_query = self._apply_scope()
        return BaseQuery.all(scoped_query)

    def first(self):
        scoped_query = self._apply_scope()
        return BaseQuery.first(scoped_query)

    def count(self):
        scoped_query = self._apply_scope()
        return BaseQuery.count(scoped_query)

    def get(self, ident):
        q = self._apply_scope().filter_by(id=ident)
        return q.first()
