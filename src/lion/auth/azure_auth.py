from flask import Flask, request, jsonify, g, redirect, session

from lion.auth.load_openid import validate_token
from lion.auth.auth_config import AUTH_URL



def init_azure_auth(app: Flask):
    @app.before_request
    def authenticate():
        if (
            request.path.startswith("/static")
            or request.path in ("/health-check", "/auth/callback", "/login", "/logout", "/userinfo")
        ):
            return
        
        auth = request.headers.get("Authorization")
        if not auth or not auth.startswith("Bearer "):
            return redirect(AUTH_URL)
        
        token = auth.split(" ")[1]
        try:
            claims = validate_token(token)
            session["user"] = {
                "user_id": claims.get("sub"),
                "email": claims.get("preferred_username"),
                "name": claims.get("name"),
                "groups": claims.get("groups", []),
            }
            g.user = claims
        except Exception as e:
            session.pop("user", None)
            return jsonify({"error": "Token validation failed", "details": str(e)}), 401


    # @app.before_request
    # def set_session_context():
    #     if "user" not in session:
    #         return  # no authenticated user yet

    #     user_info = session["user"]
    #     user_id = user_info.get("email") or user_info.get("user_id")
    #     groups = user_info.get("groups", [])

    #     if not user_id:
    #         return

    #     # Flatten groups into a CSV string (for multi-group users)
    #     group_str = ",".join(groups) if groups else "unknown_group"

    #     # Now set the SQL session context for this connection
    #     try:
    #         with LION_SQLALCHEMY_DB.engine.connect() as conn:
    #             conn.execute(
    #                 text("EXEC sp_set_session_context @key=N'user_id', @value=:uid"),
    #                 {"uid": user_id},
    #             )
    #             conn.execute(
    #                 text("EXEC sp_set_session_context @key=N'group_list', @value=:glist"),
    #                 {"glist": group_str},
    #             )
    #     except Exception as e:
    #         current_app.logger.error(f"Failed to set SQL session context: {e}")


# @event.listens_for(LION_SQLALCHEMY_DB.engine, "checkout")
# def set_sql_session_context(dbapi_connection, connection_record, connection_proxy):
#     # For a high-traffic app, a cleaner pattern is to let SQLAlchemy automatically set the session 
#     # context whenever it reuses a pooled connection:

#     from flask import session
#     if "user" not in session:
#         return
    
#     user_info = session["user"]
#     user_id = user_info.get("email") or user_info.get("user_id")
#     groups = user_info.get("groups", [])
#     group_str = ",".join(groups) if groups else "unknown_group"

#     cursor = dbapi_connection.cursor()
#     cursor.execute("EXEC sp_set_session_context @key='user_id', @value=?", user_id)
#     cursor.execute("EXEC sp_set_session_context @key='group_list', @value=?", group_str)
#     cursor.close()

#     # This will help confirm that the session context is being applied correctly per user request.
#     current_app.logger.debug(f"SQL context set for user={user_id}, groups={group_str}")