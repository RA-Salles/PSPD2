from flask import Blueprint, jsonify, g, request
import grpc
import requests
import json

import auth_pb2
import auth_pb2_grpc

import patient_pb2
import patient_pb2_grpc

api_bp = Blueprint("api", __name__, url_prefix="/api")

auth_channel = grpc.insecure_channel('localhost:50051')
auth_stub = auth_pb2_grpc.AuthServiceStub(auth_channel)

patient_channel = grpc.insecure_channel('localhost:50052')
patient_stub = patient_pb2_grpc.PatientDataServiceStub(patient_channel)

@api_bp.route("/public")
def public_endpoint():
    """Accessible without authentication."""
    return jsonify({"message": "Endpoint público"})

@api_bp.route("/protected")

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

def admin_endpoint():
    """Requer admin para acessar."""
    return jsonify(
        {
            "message": "Bem-vindo, admin",
            "username": g.username,
        }
    )

@api_bp.route("/manager")

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

def buscar_paciente(paciente_id):
    auth_header = request.headers.get('Authorization')
    token_jwt = auth_header.split(" ")[1]

    try:
        auth_req = auth_pb2.AuthRequest(
            jwt_token       = token_jwt,
            requested_scope = "ResumoClinico", 
            target_id       = paciente_id
        )
        auth_resposta = auth_stub.VerifyAccess(auth_req)
        
    except grpc.RpcError as e:
        return jsonify({"erro": "Serviço de autorização indisponível"}), 500

    if auth_resposta.access_level == "DENY":
        return jsonify({"erro": "Acesso negado pelas regras do hospital"}), 403

    if auth_resposta.access_level == "DENY":
        return jsonify({"erro": "Acesso negado pelas regras do hospital"}), 403

    try:
        patient_req = patient_pb2.SinglePatientRequest(
            patient_id   = paciente_id,
            access_level = auth_resposta.access_level
        )
        patient_data = patient_stub.GetSinglePatientData(patient_req)
        
        try:
            dados_fhir = json.loads(patient_data.raw_database_json)
        except:
            dados_fhir = patient_data.raw_database_json

        return jsonify({
            "mensagem"         : "Acesso autorizado",
            "nivel_concedido"  : auth_resposta.access_level,
            "resposta"         : dados_fhir
        }), 200
        
    except grpc.RpcError as e:
        if e.code() == grpc.StatusCode.NOT_FOUND:
            return jsonify({"erro": "Paciente não existe no banco de dados."}), 404
            
        return jsonify({"erro": f"Falha nos microsserviços: {e.details()}"}), 500

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