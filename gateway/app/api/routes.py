from flask import Blueprint, jsonify, g
from app.auth.decorators import require_auth, require_role

api_bp = Blueprint("api", __name__, url_prefix="/api")

@api_bp.route("/public")
def public_endpoint():
    """Accessible without authentication."""
    return jsonify({"message": "This is a public endpoint"})

@api_bp.route("/protected")
@require_auth
def protected_endpoint():
    """Requires a valid access token."""
    return jsonify(
        {
            "message": "You are authenticated",
            "user_id": g.user_id,
            "username": g.username,
            "email": g.email,
            "roles": g.roles,
        }
    )

@api_bp.route("/admin")
@require_role("admin")
def admin_endpoint():
    """Requires the admin role."""
    return jsonify(
        {
            "message": "Welcome, admin",
            "username": g.username,
        }
    )

@api_bp.route("/manager")
@require_role("admin", "manager")
def manager_endpoint():
    """Requires admin or manager role."""
    return jsonify(
        {
            "message": "Welcome to the management area",
            "username": g.username,
            "roles": g.roles,
        }
    )

@api_bp.route("/profile")
@require_auth
def user_profile():
    """Return the full decoded token payload."""
    return jsonify(
        {
            "sub": g.user_id,
            "preferred_username": g.username,
            "email": g.email,
            "roles": g.roles,
            "token_claims": {
                k: v
                for k, v in g.token_payload.items()
                if k
                not in ("exp", "iat", "auth_time", "jti", "typ", "azp", "sid")
            },
        }
    )