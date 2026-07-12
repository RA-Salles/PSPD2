from flask import Blueprint, jsonify, g, request
import grpc
from app.auth.decorators import require_auth, require_role
import requests

import auth_pb2
import auth_pb2_grpc

api_bp = Blueprint("api", __name__, url_prefix="/api")

auth_channel = grpc.insecure_channel('localhost:50051')
auth_stub = auth_pb2_grpc.AuthServiceStub(auth_channel)

@api_bp.route("/public")
def public_endpoint():
    """Accessible without authentication."""
    return jsonify({"message": "Endpoint público"})

@api_bp.route("/protected")
@require_auth
def protected_endpoint():
    """Requer token válido."""
    return jsonify(
        {
            "message": "autenticação bem-sucedida",
            "user_id": g.user_id,
            "username": g.username,
            "email": g.email,
            "roles": g.roles,
        }
    )

@api_bp.route("/admin")
@require_role("admin")
def admin_endpoint():
    """Requer admin para acessar."""
    return jsonify(
        {
            "message": "Bem-vindo, admin",
            "username": g.username,
        }
    )

@api_bp.route("/manager")
@require_role("admin", "manager")
def manager_endpoint():
    """Requer admin ou manager para acessar."""
    return jsonify(
        {
            "message": "Bem-vindo à área de gestão",
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

@api_bp.route("/pacientes/<paciente_id>", methods=['GET'])
@require_auth 
def buscar_paciente(paciente_id):
    auth_header = request.headers.get('Authorization')
    token_jwt = auth_header.split(" ")[1]

    try:
        auth_req = auth_pb2.AuthRequest(
            jwt_token=token_jwt,
            requested_scope="ResumoClinico", 
            target_id=paciente_id
        )
        auth_resposta = auth_stub.VerifyAccess(auth_req)
        
    except grpc.RpcError as e:
        return jsonify({"erro": "Serviço de autorização indisponível"}), 500

    if auth_resposta.access_level == "DENY":
        return jsonify({"erro": "Acesso negado pelas regras do hospital"}), 403

    return jsonify({
        "mensagem": "Acesso autorizado",
        "nivel_concedido": auth_resposta.access_level,
        "usuario_keycloak": g.username 
    })

@api_bp.route("/login", methods=["POST"])
def proxy_login():
    """Rota que serve de ponte entre o Frontend e o Keycloak para burlar o CORS"""
    dados = request.get_json()
    username = dados.get("username")
    password = dados.get("password")

    payload = {
        "client_id": "admin-cli", 
        "grant_type": "password",
        "username": username,
        "password": password,
        "scope": "openid"
    }
    
    try:
        keycloak_url = "https://kiriland.unb.br/keycloak/realms/grupo02/protocol/openid-connect/token"
        resposta_keycloak = requests.post(keycloak_url, data=payload)
        
        if resposta_keycloak.status_code == 200:
            return jsonify(resposta_keycloak.json()), 200
        else:
            return jsonify({"erro": "Usuário ou senha inválidos"}), 401
            
    except Exception as e:
        return jsonify({"erro": f"Erro de comunicação com Keycloak: {str(e)}"}), 500