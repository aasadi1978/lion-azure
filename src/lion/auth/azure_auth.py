from os import getenv
from flask import Blueprint, current_app, request, jsonify, g, redirect, session
import jwt
import requests
import urllib.parse
from sqlalchemy import event
from sqlalchemy import text

from lion.create_flask_app.extensions import LION_SQLALCHEMY_DB


auth_bp = Blueprint("auth", __name__)

REDIRECT_URI = "http://localhost:8080/auth/callback"
TENANT_ID = getenv("AZURE_LION_APP_TENANT_ID")
CLIENT_ID = getenv("AZURE_LION_APP_CLIENT_ID")
CLIENT_SECRET = getenv("AZURE_LION_APP_CLIENT_SECRET")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
OPENID_CONFIG_URL = f"{AUTHORITY}/.well-known/openid-configuration"

AUTH_URL = (
    f"{AUTHORITY}/oauth2/v2.0/authorize?"
    f"client_id={CLIENT_ID}"
    f"&response_type=code"
    f"&redirect_uri={urllib.parse.quote(REDIRECT_URI)}"
    f"&scope=openid profile email offline_access"
)

# Load OIDC configuration
openid_config = requests.get(OPENID_CONFIG_URL).json()
issuer = openid_config["issuer"]
jwks_uri = openid_config["jwks_uri"]
jwks_keys = requests.get(jwks_uri).json()["keys"]

def validate_token(token):
    header = jwt.get_unverified_header(token)
    key = next((k for k in jwks_keys if k["kid"] == header["kid"]), None)
    if not key:
        raise Exception("Matching public key not found")
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
    return jwt.decode(token, public_key, algorithms=["RS256"], audience=CLIENT_ID, issuer=issuer)

@auth_bp.route("/login")
def login():
    session.pop("user", None)
    return redirect(AUTH_URL)

@auth_bp.route("/auth/callback")
def auth_callback():
    code = request.args.get("code")
    if not code:
        return jsonify({"error": "Missing code"}), 400

    token_response = requests.post(
        f"{AUTHORITY}/oauth2/v2.0/token",
        data={
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "scope": "openid profile email offline_access",
            "code": code,
            "redirect_uri": REDIRECT_URI,
            "grant_type": "authorization_code"
        },
    )

    token = token_response.json()
    access_token = token.get("access_token")
    if not access_token:
        return jsonify({"error": "Failed to obtain access token", "details": token}), 400

    claims = validate_token(access_token)
    session["access_token"] = access_token
    session["user"] = {
        "email": claims.get("preferred_username"),
        "name": claims.get("name"),
        "groups": claims.get("groups", []),
    }
    return redirect("/")

def init_azure_auth(app):
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


    @app.before_request
    def set_session_context():
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
            current_app.logger.error(f"Failed to set SQL session context: {e}")


@event.listens_for(LION_SQLALCHEMY_DB.engine, "checkout")
def set_sql_session_context(dbapi_connection, connection_record, connection_proxy):
    # For a high-traffic app, a cleaner pattern is to let SQLAlchemy automatically set the session 
    # context whenever it reuses a pooled connection:

    from flask import session
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
    current_app.logger.debug(f"SQL context set for user={user_id}, groups={group_str}")