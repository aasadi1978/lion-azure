from os import getenv
import urllib


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
