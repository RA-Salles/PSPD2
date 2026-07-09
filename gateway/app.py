from flask import Flask, request, jsonify
import grpc

import hospital_pb2
import hospital_pb2_grpc

app = Flask(__name__)

# Configura o canalpara conversar com Auth
auth_channel = grpc.insecure_channel('localhost:50051')
auth_stub = hospital_pb2_grpc.AuthServiceStub(auth_channel)

@app.route('/api/pacientes/<paciente_id>', methods=['GET'])
def buscar_paciente(paciente_id):
    # pega o token do cabeçalho da requisicao HTTP 
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith("Bearer "):
        return jsonify({"erro": "Token não fornecido"}), 401
    
    token_jwt = auth_header.split(" ")[1]

    # faz a chamada para o auth
    try:
        # Monta a requisição com o proto
        auth_req = hospital_pb2.AuthRequest(
            jwt_token=token_jwt,
            requested_scope="ResumoClinico",
            target_id=paciente_id
        )
        # verifica acesso
        auth_resposta = auth_stub.VerifyAccess(auth_req)
        
    except grpc.RpcError as e:
        return jsonify({"erro": "Serviço de autenticação indisponível"}), 500

    # verifica resposta
    if auth_resposta.access_level == "DENY":
        return jsonify({"erro": "Acesso negado"}), 403

    # aqui sera o para chamar o PatientDataService passando o access_level
    
    return jsonify({
        "mensagem": "Acesso autorizado",
        "nivel_concedido": auth_resposta.access_level
    })

if __name__ == '__main__':
    app.run(port=5000)