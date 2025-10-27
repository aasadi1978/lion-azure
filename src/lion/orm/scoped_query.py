from sqlalchemy.orm import Query as BaseQuery
from flask import has_request_context, session, g
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

    _current_user = {'scn_id': int(getattr(g, "current_scn_id", 0)) or int(session.get("current_scn_id", 0)),
                    'user_id': session.get("_current_user", {}).get('user_id', '') or g.get("_current_user", {}).get('user_id', '')}

    _current_group = session.get("current_group", None) or g.get("current_group", None)

    def _apply_scope(self):

        try:

            if not has_request_context():
                return self
            
            if not self._current_user.get('user_id', ''):
                return self
            
            entity = self._only_full_mapper_zero("apply_scope").class_
            hierarchy = getattr(entity, "__scope_hierarchy__", ["group_name"])

            if hierarchy == []:
                return self

            filters = []

            for scope_field in hierarchy:

                if not hasattr(entity, scope_field):
                    continue

                user_field = self._user_field_map.get(scope_field)
                if not hasattr(self._current_user, user_field):
                    continue


                if scope_field=='group_name' and hasattr(entity, "group_name"):

                    if not self._current_group:
                        raise Exception('Unknown group name.')

                    filters.append(getattr(entity, "group_name", '') == self._current_group)
                    continue

                user_value = getattr(self._current_user, user_field)
                if user_value is not None:
                    filters.append(getattr(entity, scope_field) == user_value)

            # Apply logic based on declared hierarchy
            if not filters:
                return self

            condition = and_(*filters)
            return self.enable_assertions(False).filter(condition)
        
        except Exception:
            log_exception('_apply_scope failed.')
            return self

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
        return BaseQuery.__iter__(self._apply_scope())
        # return super(AutoScopedQuery, self)._apply_scope().__iter__()

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
