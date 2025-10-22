from os import getenv
from flask import request, jsonify, g
import jwt
import requests
from lion.create_flask_app.create_app import LION_FLASK_APP


TENANT_ID = getenv("AZURE_LION_APP_TENANT_ID")
CLIENT_ID = getenv("AZURE_LION_APP_CLIENT_ID")
AUTHORITY = f"https://login.microsoftonline.com/{TENANT_ID}/v2.0"
OPENID_CONFIG_URL = f"{AUTHORITY}/.well-known/openid-configuration"

"""
How It Works

When a request is made to /api/userinfo, the Flask app:
Extracts the Authorization token
Validates it using public keys from Microsoft Entra
Decodes the token to get user info and group claims
Returns them in the response
"""

# Fetch OpenID Connect config
openid_config = requests.get(OPENID_CONFIG_URL).json()
issuer = openid_config["issuer"]
jwks_uri = openid_config["jwks_uri"]
jwks_keys = requests.get(jwks_uri).json()["keys"]

def validate_token(token):
    # Decode token header
    header = jwt.get_unverified_header(token)
    key = next((k for k in jwks_keys if k["kid"] == header["kid"]), None)
    if not key:
        raise Exception("Matching public key not found")
    
    public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)

    # Decode and verify token
    decoded = jwt.decode(
        token,
        public_key,
        algorithms=["RS256"],
        audience=CLIENT_ID,
        issuer=issuer
    )
    return decoded

@LION_FLASK_APP.before_request
def authenticate():
    auth = request.headers.get("Authorization", None)
    if not auth or not auth.startswith("Bearer "):
        return jsonify({"error": "Missing or invalid Authorization header"}), 401

    token = auth.split(" ")[1]
    try:
        claims = validate_token(token)
        g.user = claims  # Save user claims in global context
    except Exception as e:
        return jsonify({"error": "Token validation failed", "details": str(e)}), 401

@LION_FLASK_APP.route("/api/userinfo")
def userinfo():
    user = g.user
    return jsonify({
        "user_id": user.get("sub"),
        "email": user.get("preferred_username"),
        "groups": user.get("groups", [])
    })
