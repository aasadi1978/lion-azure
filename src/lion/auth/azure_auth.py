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
