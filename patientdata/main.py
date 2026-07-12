import os #novo import pra definir portas pro banco
import grpc
from concurrent import futures
import json
import psycopg2
from psycopg2.extras import RealDictCursor

import patient_pb2
import patient_pb2_grpc

import transform_pb2
import transform_pb2_grpc


# Configurações do Banco de Dados 
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "5432"))
DB_NAME = os.getenv("DB_NAME", "pseudopep_g02")
DB_USER = os.getenv("DB_USER", "grupo02_user")
DB_PASS = os.getenv("DB_PASS", "")

# Conexão do cliente gRPC pro Data Transform
DATA_TRANSFORM_ADDRESS = "localhost:50053"

#Quando formos migrar pro kubernetes:
# DATA_TRANSFORM_ADDRESS = "data-transform:50053"

transform_channel = grpc.insecure_channel(DATA_TRANSFORM_ADDRESS)

transform_stub = transform_pb2_grpc.DataTransformServiceStub(
    transform_channel
)


# Lógica do Microsserviço

class PatientDataServiceServicer(patient_pb2_grpc.PatientDataServiceServicer):

    def _conectar_banco(self):
        """Estabelece a conexão com o banco de dados retornando dicionários."""
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASS,
            cursor_factory=RealDictCursor
        )

    def GetSinglePatientData(self, request, context):
        """
        Chamada Unaria: Busca todos os dados brutos de um único paciente.
        Acionada quando o nível de acesso é FULL ou PARTIAL.
        """
        id_paciente_alvo = request.patient_id
        nivel_acesso_concedido = request.access_level
        
        # Estrutura base da resposta
        dados_empacotados = {
            "nivel_permitido": nivel_acesso_concedido,
            "paciente": None,
            "atendimentos": [],
            "eventos_clinicos": []
        }

        try:
            conexao = self._conectar_banco()
            cursor = conexao.cursor()
                    
            # Busca os dados demográficos
            cursor.execute(
                "SELECT * FROM patients WHERE patient_id = %s",
                (id_paciente_alvo,)
            )
            dados_empacotados["paciente"] = cursor.fetchone()

            # Busca os atendimentos
            cursor.execute(
                """
                SELECT *
                FROM encounters
                WHERE patient_id = %s
                ORDER BY start_date
                """,
                (id_paciente_alvo,)
            )

            dados_empacotados["atendimentos"] = cursor.fetchall()
                    
            # Busca o histórico clínico
            cursor.execute(
                """
                SELECT *
                FROM clinical_events
                WHERE patient_id = %s
                ORDER BY event_date
                """,
                (id_paciente_alvo,)
            )
            dados_empacotados["eventos_clinicos"] = cursor.fetchall()
                    
            cursor.close()
            conexao.close()

            if not dados_empacotados["paciente"]:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details("Paciente nao encontrado no banco de dados.")
                return patient_pb2.PatientDataResponse()

            # REFATORADO - Converte os registros do banco para JSON
            payload_em_json = json.dumps(
                dados_empacotados,
                default=str,
                ensure_ascii=False
            )

            # Envia os dados brutos para o Data Transform
            resposta_transformada = transform_stub.TransformToFHIR(
                transform_pb2.TransformRequest(
                    raw_database_json=payload_em_json,
                    access_level=nivel_acesso_concedido
                ),
                timeout=10
            )

            # Retorna o JSON FHIR ao chamador
            return patient_pb2.PatientDataResponse(
                raw_database_json=resposta_transformada.fhir_json_payload
            )

        except Exception as erro_execucao:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Falha interna no banco: {str(erro_execucao)}")
            return patient_pb2.PatientDataResponse()

    def StreamCohortData(self, request, context):
        """
        Server Streaming: Busca pacientes aos poucos para não derrubar a memória.
        Acionada por pesquisadores com nível ANONYMIZED.
        """
        codigo_da_condicao = request.condition_code
        nivel_acesso_concedido = request.access_level
        
        try:
            conexao = self._conectar_banco()
            cursor = conexao.cursor(name="cursor_pesquisa_coorte")
            
            consulta_sql = """
                SELECT DISTINCT p.*
                FROM patients p
                JOIN clinical_events c
                ON p.patient_id = c.patient_id
                WHERE c.code = %s
            """
            cursor.execute(consulta_sql, (codigo_da_condicao,))
            
            # Processa e envia 100 pacientes por vez
            while True:
                lote_atual = cursor.fetchmany(100)
                if not lote_atual:
                    break # Acabaram os dados
                
                pacote_resposta = {
                    "nivel_permitido": nivel_acesso_concedido,
                    "tamanho_lote": len(lote_atual),
                    "lote_coorte": lote_atual
                }
                
                payload_em_json = json.dumps(
                pacote_resposta,
                default=str,
                ensure_ascii=False
            )

            resposta_transformada = transform_stub.TransformToFHIR(
                transform_pb2.TransformRequest(
                    raw_database_json=payload_em_json,
                    access_level=nivel_acesso_concedido
                ),
                timeout=10
            )

            yield patient_pb2.PatientDataResponse(
                raw_database_json=resposta_transformada.fhir_json_payload
            )
                
            cursor.close()
            conexao.close()
            
        except Exception as erro_execucao:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Falha no streaming do banco: {str(erro_execucao)}")


def iniciar_servidor():
    servidor_grpc = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    patient_pb2_grpc.add_PatientDataServiceServicer_to_server(PatientDataServiceServicer(), servidor_grpc)
    servidor_grpc.add_insecure_port('[::]:50052')
    
    print("Microsserviço de Dados de Pacientes rodando na porta 50052...")
    servidor_grpc.start()
    servidor_grpc.wait_for_termination()

if __name__ == '__main__':
    iniciar_servidor()