# lion/orm_azure/scoped_mixins.py
from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.orm_azure.scoped_query import GroupScopedQuery, UserScopedQuery

class GroupScopedBase:
    """Mixin for tables that are group_name scoped."""
    query_class = GroupScopedQuery


class UserScopedBase:
    """Mixin for tables that are user_id scoped."""
    query_class = UserScopedQuery

BASE = LION_SQLALCHEMY_DB.Model