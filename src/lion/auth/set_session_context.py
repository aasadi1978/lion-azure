from flask import Flask
from requests import session
from sqlalchemy import text

from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB
from lion.logger.exception_logger import log_exception

def set_session_context(app: Flask):

    with app.app_context():
        @app.before_request
        def set_context():
            if "user" not in session:
                return  # no authenticated user yet

            user_info = session["user"]
            user_id = user_info.get("email") or user_info.get("user_id")
            groups = user_info.get("groups", [])

            if not user_id:
                return

            # Flatten groups into a CSV string (for multi-group users)
            group_str = ",".join(groups) if groups else "unknown_group"

            # Now set the SQL session context for this connection
            try:
                with LION_SQLALCHEMY_DB.engine.connect() as conn:
                    conn.execute(
                        text("EXEC sp_set_session_context @key=N'user_id', @value=:uid"),
                        {"uid": user_id},
                    )
                    conn.execute(
                        text("EXEC sp_set_session_context @key=N'group_list', @value=:glist"),
                        {"glist": group_str},
                    )
            except Exception as e:
                log_exception(f"Failed to set SQL session context: {e}")