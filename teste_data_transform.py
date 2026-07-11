import json
import sys
from pathlib import Path

import grpc


# Adiciona a pasta datatransf ao caminho de importação
PROJECT_ROOT = Path(__file__).resolve().parent
DATA_TRANSFORM_DIR = PROJECT_ROOT / "datatransf"

sys.path.insert(0, str(DATA_TRANSFORM_DIR))


# evita de ter que copiar e colar os arquivos de nv
import transform_pb2
import transform_pb2_grpc


dados_teste = {
    "paciente": {
        "id_paciente": "P000001",
        "nome": "João da Silva",
        "data_nascimento": "1970-05-10",
        "genero": "M",
        "cidade": "Brasília",
        "estado": "DF",
        "cpf": "12345678900",
        "cns": "123456789012345"
    },
    "atendimentos": [
        {
            "id_atendimento": "A000001",
            "id_paciente": "P000001",
            "data_inicio": "2026-07-10T10:00:00",
            "data_fim": "2026-07-10T11:00:00",
            "tipo_atendimento": "Ambulatorial",
            "setor": "Endocrinologia"
        }
    ],
    "eventos_clinicos": [
        {
            "id_evento": "E000001",
            "id_paciente": "P000001",
            "id_atendimento": "A000001",
            "tipo_evento": "Condição clínica",
            "codigo_tipo_evento": "DIABETES",
            "descricao_evento": "Diabetes Tipo 2",
            "data_evento": "2026-07-10"
        },
        {
            "id_evento": "E000002",
            "id_paciente": "P000001",
            "id_atendimento": "A000001",
            "tipo_evento": "Observação",
            "codigo_tipo_evento": "GLICOSE",
            "descricao_evento": "Glicemia",
            "data_evento": "2026-07-10",
            "valor": 182,
            "unidade": "mg/dL"
        },
        {
            "id_evento": "E000003",
            "id_paciente": "P000001",
            "id_atendimento": "A000001",
            "tipo_evento": "Medicação",
            "codigo_tipo_evento": "METFORMINA",
            "descricao_evento": "Metformina",
            "data_evento": "2026-07-10",
            "valor": 850,
            "unidade": "mg"
        }
    ]
}


def testar(nivel):
    channel = grpc.insecure_channel("localhost:50053")
    stub = transform_pb2_grpc.DataTransformServiceStub(channel)

    resposta = stub.TransformToFHIR(
        transform_pb2.TransformRequest(
            raw_database_json=json.dumps(
                dados_teste,
                ensure_ascii=False
            ),
            access_level=nivel
        ),
        timeout=10
    )

    resultado = json.loads(resposta.fhir_json_payload)

    print(f"\n===== NÍVEL {nivel} =====")
    print(
        json.dumps(
            resultado,
            indent=2,
            ensure_ascii=False
        )
    )


if __name__ == "__main__":
    for nivel in [
        "FULL",
        "PARTIAL",
        "ANONYMIZED",
        "AGGREGATED"
    ]:
        testar(nivel)