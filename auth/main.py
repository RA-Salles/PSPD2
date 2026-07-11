import grpc
from concurrent import futures
import jwt
import auth_pb2
import auth_pb2_grpc

SECRET_KEY = "PSPD2SecretKey"  # Chave secreta para decodificar o JWT

import auth_pb2
import auth_pb2_grpc

class AuthServiceServicer(auth_pb2_grpc.AuthServiceServicer):
    def VerifyAccess(self, request, context):
        # campos da mensagem proto
        token = request.jwt_token
        escopo = request.requested_scope
        alvo = request.target_id
        
        try:
            # decodifica o token 
            payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            
            # lógica de negócio real.
            cargo = payload.get("cargo")
            if cargo == "medico" and escopo == "ResumoClinico":
                nivel_acesso = "FULL" 
            elif cargo == "pesquisador" and escopo == "ResumoCoorte":
                nivel_acesso = "ANONYMIZED"
            else:
                nivel_acesso = "DENY"
                
            return auth_pb2.AuthResponse(access_level=nivel_acesso)
            
        except jwt.ExpiredSignatureError:
             return auth_pb2.AuthResponse(access_level="DENY")
        except jwt.InvalidTokenError:
             return auth_pb2.AuthResponse(access_level="DENY")

def serve():
    # Inicia o servidor na porta 50051
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    auth_pb2_grpc.add_AuthServiceServicer_to_server(AuthServiceServicer(), server)
    server.add_insecure_port('[::]:50051')
    print("Microsserviço de Autenticação rodando na porta 50051...")
    server.start()
    server.wait_for_termination()

if __name__ == '__main__':
    serve()