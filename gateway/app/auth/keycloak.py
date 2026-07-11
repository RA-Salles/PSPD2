import jwt
import requests
from functools import lru_cache
from jwt import PyJWKClient
from flask import current_app

@lru_cache(maxsize=1)
def get_jwk_client() -> PyJWKClient:
    """Create a cached JWK client for token verification."""
    config = current_app.config
    jwks_uri = (
        f"{config['KEYCLOAK_URL']}/realms/{config['KEYCLOAK_REALM']}"
        f"/protocol/openid-connect/certs"
    )
    return PyJWKClient(jwks_uri)

def validate_token(token: str) -> dict:
    """
    Validate a JWT access token from Keycloak.

    Returns the decoded token payload if valid.
    Raises jwt.InvalidTokenError or subclasses on failure.
    """
    config = current_app.config
    issuer = (
        f"{config['KEYCLOAK_URL']}/realms/{config['KEYCLOAK_REALM']}"
    )

    jwk_client = get_jwk_client()
    signing_key = jwk_client.get_signing_key_from_jwt(token)

    decoded = jwt.decode(
        token,
        signing_key.key,
        algorithms=["RS256"],
        issuer=issuer,
        options={
            "verify_aud": False,  # Keycloak access tokens may not have aud
            "verify_exp": True,
            "verify_iss": True,
        },
    )

    return decoded

def get_user_roles(token_payload: dict) -> list[str]:
    """Extract realm roles from a decoded Keycloak token."""
    realm_access = token_payload.get("realm_access", {})
    return realm_access.get("roles", [])

def get_client_roles(token_payload: dict, client_id: str) -> list[str]:
    """Extract client-specific roles from a decoded Keycloak token."""
    resource_access = token_payload.get("resource_access", {})
    client_access = resource_access.get(client_id, {})
    return client_access.get("roles", [])

def exchange_code_for_tokens(code: str, redirect_uri: str) -> dict:
    """Exchange an authorization code for tokens."""
    config = current_app.config
    token_url = (
        f"{config['KEYCLOAK_URL']}/realms/{config['KEYCLOAK_REALM']}"
        f"/protocol/openid-connect/token"
    )

    response = requests.post(
        token_url,
        data={
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": config["KEYCLOAK_CLIENT_ID"],
            "client_secret": config["KEYCLOAK_CLIENT_SECRET"],
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()

def refresh_access_token(refresh_token: str) -> dict:
    """Use a refresh token to get new access and refresh tokens."""
    config = current_app.config
    token_url = (
        f"{config['KEYCLOAK_URL']}/realms/{config['KEYCLOAK_REALM']}"
        f"/protocol/openid-connect/token"
    )

    response = requests.post(
        token_url,
        data={
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": config["KEYCLOAK_CLIENT_ID"],
            "client_secret": config["KEYCLOAK_CLIENT_SECRET"],
        },
        timeout=10,
    )

    response.raise_for_status()
    return response.json()