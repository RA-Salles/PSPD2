import grpc
from concurrent import futures
import jwt
import auth_pb2
import auth_pb2_grpc

class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    def VerifyAccess(self, request, context):
        token = request.jwt_token
        escopo = request.requested_scope
        alvo = request.target_id
        
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            
            realm_access = payload.get("realm_access", {})
            roles = realm_access.get("roles", [])
            

            if "medico" in roles and escopo == "ResumoClinico":
                nivel_acesso = "FULL" 
            elif "estagiario" in roles and escopo == "ResumoClinico":
                nivel_acesso = "PARTIAL"
            elif "pesquisador" in roles and escopo == "ResumoCoorte":
                nivel_acesso = "ANONYMIZED"
            else:
                nivel_acesso = "DENY"
                
            return auth_pb2.AuthResponse(access_level=nivel_acesso)
            
        except Exception as e:
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