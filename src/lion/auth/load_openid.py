from functools import lru_cache
import jwt
import requests

from lion.auth.auth_config import OPENID_CONFIG_URL, CLIENT_ID
from lion.logger.exception_logger import log_exception

@lru_cache()
def get_openid_config():
    # Load OIDC configuration
    try:
        config = requests.get(OPENID_CONFIG_URL, timeout=5).json()
        if "issuer" not in config or "jwks_uri" not in config:
            raise ValueError("Missing expected keys in OpenID config")
        return config
    except Exception:
        log_exception(f"Failed to load OpenID config.")
    
    return {}

@lru_cache()
def get_jwks_keys():

    openid_configuration = get_openid_config()
    jwks_uri = openid_configuration.get("jwks_uri", "")
    if not jwks_uri:
        return []
    
    try:
        return requests.get(jwks_uri, timeout=5).json().get("keys", [])
    except Exception:
        log_exception(f"Failed to fetch JWKS keys.")

    return []

def validate_token(token):

    try:
        header = jwt.get_unverified_header(token)
        jwk_keys = get_jwks_keys() # Ensure keys are loaded
        if not jwk_keys:
            raise Exception("JWKS keys not available")
        
        key = next((k for k in jwk_keys if k["kid"] == header["kid"]), None)
        if not key:
            raise Exception("Matching public key not found")
        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        openid_configuration = get_openid_config()

        if not openid_configuration:
            raise Exception("OpenID configuration not available")
        
        return jwt.decode(token, public_key, algorithms=["RS256"], audience=CLIENT_ID, issuer=openid_configuration["issuer"])

    except Exception:
        log_exception("Token validation failed.")

    return None