import logging
from flask import session
from sqlalchemy import event

from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB


@event.listens_for(LION_SQLALCHEMY_DB.engine, "checkout")
def set_sql_session_context(dbapi_connection, connection_record, connection_proxy):
    # For a high-traffic app, a cleaner pattern is to let SQLAlchemy automatically set the session 
    # context whenever it reuses a pooled connection:

    if "user" not in session:
        return
    
    user_info = session["user"]
    user_id = user_info.get("email") or user_info.get("user_id")
    groups = user_info.get("groups", [])
    group_str = ",".join(groups) if groups else "unknown_group"

    cursor = dbapi_connection.cursor()
    cursor.execute("EXEC sp_set_session_context @key='user_id', @value=?", user_id)
    cursor.execute("EXEC sp_set_session_context @key='group_list', @value=?", group_str)
    cursor.close()

    # This will help confirm that the session context is being applied correctly per user request.
    logging.debug(f"SQL context set for user={user_id}, groups={group_str}")