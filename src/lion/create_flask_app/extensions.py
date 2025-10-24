from flask_sqlalchemy import SQLAlchemy

from lion.orm.scoped_query import AutoScopedQuery
LION_SQLALCHEMY_DB = SQLAlchemy(query_class=AutoScopedQuery)
