import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "dev-secret-key")

    KEYCLOAK_URL = os.environ.get("KEYCLOAK_URL", "http://localhost:8080")
    KEYCLOAK_REALM = os.environ.get("KEYCLOAK_REALM", "flask-api")
    KEYCLOAK_CLIENT_ID = os.environ.get("KEYCLOAK_CLIENT_ID", "flask-backend")
    KEYCLOAK_CLIENT_SECRET = os.environ.get("KEYCLOAK_CLIENT_SECRET", "")

    @property
    def KEYCLOAK_ISSUER(self) -> str:
        return f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"

    @property
    def KEYCLOAK_JWKS_URI(self) -> str:
        return (
            f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/certs"
        )

    @property
    def KEYCLOAK_TOKEN_URL(self) -> str:
        return (
            f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/token"
        )

    @property
    def KEYCLOAK_AUTH_URL(self) -> str:
        return (
            f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/auth"
        )

    @property
    def KEYCLOAK_USERINFO_URL(self) -> str:
        return (
            f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/userinfo"
        )

    @property
    def KEYCLOAK_LOGOUT_URL(self) -> str:
        return (
            f"{self.KEYCLOAK_URL}/realms/{self.KEYCLOAK_REALM}"
            f"/protocol/openid-connect/logout"
        )