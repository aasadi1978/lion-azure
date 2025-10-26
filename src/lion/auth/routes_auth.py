from os import getenv
from flask import Blueprint, request, jsonify, redirect, session
import requests

from lion.auth.load_openid import validate_token
from lion.auth.auth_config import REDIRECT_URI, CLIENT_ID, CLIENT_SECRET, AUTHORITY, AUTH_URL

auth_bp = Blueprint("auth", __name__)
DISABLE_LOGIN = getenv("DISABLE_LOGIN", "false").lower() == "true"

@auth_bp.route("/login")
def login():
    # Local dev bypass
    if DISABLE_LOGIN:
        session["user"] = {
            "email": "localuser@dev.test",
            "name": "Local Dev User",
            "groups": ["fedex-lion-developers"],
        }
        session["access_token"] = "local-dev-token"
        return redirect("/")

    # Normal Azure redirect
    session.pop("user", None)
    return redirect(AUTH_URL)


@auth_bp.route("/auth/callback")
def auth_callback():
    # If local login is bypassed, do nothing
    if DISABLE_LOGIN:
        return redirect("/")

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