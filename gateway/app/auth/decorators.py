from functools import wraps
from flask import request, jsonify, g
from app.auth.keycloak import validate_token, get_user_roles

def require_auth(f):
    """Decorator that requires a valid Keycloak access token."""

    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            return jsonify({"error": "Missing Authorization header"}), 401

        parts = auth_header.split()
        if len(parts) != 2 or parts[0].lower() != "bearer":
            return jsonify({"error": "Invalid Authorization header format"}), 401

        token = parts[1]

        try:
            payload = validate_token(token)
        except Exception as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401

        # Store decoded token and roles in Flask's g object
        g.token_payload = payload
        g.user_id = payload.get("sub")
        g.username = payload.get("preferred_username")
        g.email = payload.get("email")
        g.roles = get_user_roles(payload)

        return f(*args, **kwargs)

    return decorated

def require_role(*required_roles):
    """
    Decorator that requires the user to have at least one
    of the specified roles.

    Usage:
        @require_role("admin")
        @require_role("admin", "manager")
    """

    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated(*args, **kwargs):
            user_roles = set(g.roles)
            if not user_roles.intersection(required_roles):
                return (
                    jsonify(
                        {
                            "error": "Insufficient permissions",
                            "required_roles": list(required_roles),
                            "your_roles": list(user_roles),
                        }
                    ),
                    403,
                )
            return f(*args, **kwargs)

        return decorated

    return decorator