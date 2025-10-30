import logging
from sqlalchemy.orm import Query as BaseQuery
from flask import has_request_context
from sqlalchemy import and_
from lion.utils.session_manager import SESSION_MANAGER

class AutoScopedQuery(BaseQuery):
    """
    Automatically applies hierarchical access control based on __scope_hierarchy__.
    Supports scn_id, group_name, and user_id scopes, with model-level priority.
    __scope_hierarchy__ =  ["scn_id", "user_id", "group_name"]
    """

    def _get_current_user(self):

        scn_id = SESSION_MANAGER.get('scn_id', 0)
        user_id = SESSION_MANAGER.get('user_id', 0)
        group_name = SESSION_MANAGER.get('group_name', None)

        if scn_id and user_id and group_name and len(str(scn_id)) > 0 and len(str(user_id)) > 0 and len(str(group_name)) > 0:
            return {'scn_id': scn_id, 'user_id': user_id, 'group_name': group_name}
        
        return {}


    def _apply_scope(self):

        try:

            if not has_request_context():
                return self
            
            _current_user = self._get_current_user()
            if not _current_user:
                return self
            
            entity = self._only_full_mapper_zero("apply_scope").class_
            hierarchy = getattr(entity, "__scope_hierarchy__", ["group_name"])

            if hierarchy == []:
                return self

            filters = []
            for scope_field in hierarchy:

                _apply_filter_flag: bool = hasattr(entity, scope_field) and _current_user.get(scope_field, None)

                if _apply_filter_flag:
                    filters.append(getattr(entity, scope_field) == _current_user[scope_field])

            # Apply logic based on declared hierarchy
            if not filters:
                return self

            condition = and_(*filters)
            return self.enable_assertions(False).filter(condition)
        
        except Exception:
            logging.error('_apply_scope failed.')
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
