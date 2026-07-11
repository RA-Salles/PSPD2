from urllib.parse import urlencode
from flask import Blueprint, redirect, request, jsonify, session, current_app
from app.auth.keycloak import exchange_code_for_tokens, refresh_access_token

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")

@auth_bp.route("/login")
def login():
    """Redirect the user to Keycloak's login page."""
    config = current_app.config
    redirect_uri = request.url_root.rstrip("/") + "/auth/callback"

    auth_url = (
        f"{config['KEYCLOAK_URL']}/realms/{config['KEYCLOAK_REALM']}"
        f"/protocol/openid-connect/auth"
    )

    params = urlencode(
        {
            "client_id": config["KEYCLOAK_CLIENT_ID"],
            "response_type": "code",
            "scope": "openid email profile",
            "redirect_uri": redirect_uri,
        }
    )

    return redirect(f"{auth_url}?{params}")

@auth_bp.route("/callback")
def callback():
    """Handle the OAuth2 callback from Keycloak."""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return jsonify({"error": error}), 400

    if not code:
        return jsonify({"error": "Missing authorization code"}), 400

    redirect_uri = request.url_root.rstrip("/") + "/auth/callback"

    try:
        tokens = exchange_code_for_tokens(code, redirect_uri)
    except Exception as e:
        return jsonify({"error": f"Token exchange failed: {str(e)}"}), 500

    # In a real app, you might set these in an HTTP-only cookie
    # or return them for the frontend to store
    session["access_token"] = tokens["access_token"]
    session["refresh_token"] = tokens["refresh_token"]
    session["id_token"] = tokens.get("id_token")

    return jsonify(
        {
            "message": "Login successful",
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
        }
    )

@auth_bp.route("/refresh", methods=["POST"])
def refresh():
    """Refresh the access token using the refresh token."""
    refresh_token = request.json.get("refresh_token") if request.json else None

    if not refresh_token:
        refresh_token = session.get("refresh_token")

    if not refresh_token:
        return jsonify({"error": "No refresh token provided"}), 400

    try:
        tokens = refresh_access_token(refresh_token)
    except Exception as e:
        return jsonify({"error": f"Token refresh failed: {str(e)}"}), 401

    session["access_token"] = tokens["access_token"]
    session["refresh_token"] = tokens["refresh_token"]

    return jsonify(
        {
            "access_token": tokens["access_token"],
            "refresh_token": tokens["refresh_token"],
            "expires_in": tokens["expires_in"],
        }
    )

@auth_bp.route("/logout", methods=["POST"])
def logout():
    """Log the user out of Keycloak and clear the session."""
    config = current_app.config
    refresh_token = session.get("refresh_token")

    logout_url = (
        f"{config['KEYCLOAK_URL']}/realms/{config['KEYCLOAK_REALM']}"
        f"/protocol/openid-connect/logout"
    )

    if refresh_token:
        import requests as http_requests

        try:
            http_requests.post(
                logout_url,
                data={
                    "client_id": config["KEYCLOAK_CLIENT_ID"],
                    "client_secret": config["KEYCLOAK_CLIENT_SECRET"],
                    "refresh_token": refresh_token,
                },
                timeout=10,
            )
        except Exception:
            pass  # Best effort logout

    session.clear()
    return jsonify({"message": "Logged out successfully"})