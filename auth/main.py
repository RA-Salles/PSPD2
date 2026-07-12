import grpc
from concurrent import futures
import requests
import auth_pb2
import auth_pb2_grpc

USERINFO_URL = "https://kiriland.unb.br/keycloak/realms/grupo02/protocol/openid-connect/userinfo"

class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    def VerifyAccess(self, request, context):
        token = request.jwt_token
        escopo = request.requested_scope
        
        try:
            headers = {"Authorization": f"Bearer {token}"}
            resposta = requests.get(USERINFO_URL, headers=headers)
            
            if resposta.status_code != 200:
                print(f"DEBUG - Erro no userinfo: {resposta.text}")
                return auth_pb2.AuthResponse(access_level="DENY")
                
            dados_usuario = resposta.json()
            username = dados_usuario.get("preferred_username", "")
            
            print(f"DEBUG - Usuário autenticado com sucesso: {username}")
            
            if username.startswith("med.") and escopo == "ResumoClinico":
                nivel_acesso = "FULL" 
            elif username.startswith("est.") and escopo == "ResumoClinico":
                nivel_acesso = "PARTIAL"
            elif username.startswith("pes.") and escopo == "ResumoCoorte":
                nivel_acesso = "ANONYMIZED"
            else:
                nivel_acesso = "DENY"
                
            return auth_pb2.AuthResponse(access_level=nivel_acesso)
            
        except Exception as e:
            print(f"DEBUG - Falha na autorização: {str(e)}")
            return auth_pb2.AuthResponse(access_level="DENY")

def serve():
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Microsserviço de Autorização rodando na porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()