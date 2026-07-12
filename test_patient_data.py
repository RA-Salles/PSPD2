import json
import sys
from pathlib import Path

import grpc


# ---------------------------------------------------------
# Configuração dos caminhos
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent
PATIENT_DATA_DIR = PROJECT_ROOT / "patientdata"

# Os arquivos gerados pelo gRPC utilizam imports absolutos.
# Por isso, adicionamos patientdata ao caminho de módulos.
sys.path.insert(0, str(PATIENT_DATA_DIR))

import patient_pb2
import patient_pb2_grpc


# ---------------------------------------------------------
# Configuração do teste
# ---------------------------------------------------------

PATIENT_DATA_ADDRESS = "localhost:50052"

# Paciente real encontrado no banco pseudopep_g02
PATIENT_ID = "P020008105"

# Valores possíveis:
# FULL, PARTIAL ou ANONYMIZED
ACCESS_LEVELS = [
    "FULL",
    "PARTIAL",
    "ANONYMIZED",
]


# ---------------------------------------------------------
# Funções auxiliares
# ---------------------------------------------------------

def encontrar_recursos(bundle, resource_type):
    """
    Retorna todos os recursos de determinado tipo presentes
    no Bundle FHIR.
    """
    recursos = []

    for entrada in bundle.get("entry", []):
        recurso = entrada.get("resource", {})

        if recurso.get("resourceType") == resource_type:
            recursos.append(recurso)

    return recursos


def validar_identidade(patient, access_level):
    """
    Verifica se os campos de identidade foram preservados ou
    removidos conforme o nível de acesso.
    """
    erros = []

    patient_id = patient.get("id", "")
    possui_nome = bool(patient.get("name"))
    possui_nascimento_exato = "birthDate" in patient
    possui_identificadores = bool(patient.get("identifier"))

    if access_level == "FULL":
        if patient_id != PATIENT_ID:
            erros.append(
                "FULL deveria manter o patient_id real."
            )

        if not possui_nome:
            erros.append(
                "FULL deveria apresentar o nome."
            )

        if not possui_nascimento_exato:
            erros.append(
                "FULL deveria apresentar birthDate."
            )

        if not possui_identificadores:
            erros.append(
                "FULL deveria apresentar CPF/CNS em identifier."
            )

    elif access_level == "PARTIAL":
        if patient_id != PATIENT_ID:
            erros.append(
                "PARTIAL deveria manter o patient_id real."
            )

        if not possui_nome:
            erros.append(
                "PARTIAL deveria apresentar as iniciais."
            )

        if possui_nascimento_exato:
            erros.append(
                "PARTIAL não deveria apresentar birthDate exata."
            )

        if possui_identificadores:
            erros.append(
                "PARTIAL não deveria apresentar CPF/CNS."
            )

    elif access_level == "ANONYMIZED":
        if patient_id == PATIENT_ID:
            erros.append(
                "ANONYMIZED expôs o patient_id real."
            )

        if not patient_id.startswith("anon-"):
            erros.append(
                "ANONYMIZED deveria produzir ID iniciado por anon-."
            )

        if possui_nome:
            erros.append(
                "ANONYMIZED não deveria apresentar o nome."
            )

        if possui_nascimento_exato:
            erros.append(
                "ANONYMIZED não deveria apresentar birthDate exata."
            )

        if possui_identificadores:
            erros.append(
                "ANONYMIZED não deveria apresentar CPF/CNS."
            )

    return erros


def validar_referencias(bundle, patient_id_esperado):
    """
    Confere se Encounter, Condition, Observation e
    MedicationRequest apontam para o Patient correto.
    """
    erros = []

    tipos_clinicos = {
        "Encounter",
        "Condition",
        "Observation",
        "MedicationRequest",
    }

    referencia_esperada = f"Patient/{patient_id_esperado}"

    for entrada in bundle.get("entry", []):
        recurso = entrada.get("resource", {})
        tipo = recurso.get("resourceType")

        if tipo not in tipos_clinicos:
            continue

        referencia = recurso.get(
            "subject",
            {}
        ).get("reference")

        if referencia != referencia_esperada:
            erros.append(
                f"{tipo} {recurso.get('id')} possui referência "
                f"{referencia!r}; esperado {referencia_esperada!r}."
            )

    return erros


def imprimir_resumo(bundle):
    """
    Imprime uma contagem dos recursos do Bundle.
    """
    tipos = {}

    for entrada in bundle.get("entry", []):
        recurso = entrada.get("resource", {})
        tipo = recurso.get("resourceType", "Desconhecido")

        tipos[tipo] = tipos.get(tipo, 0) + 1

    print(f"Bundle total informado: {bundle.get('total')}")
    print("Recursos encontrados:")

    for tipo, quantidade in sorted(tipos.items()):
        print(f"  {tipo}: {quantidade}")

    return tipos


# ---------------------------------------------------------
# Execução do teste
# ---------------------------------------------------------

def testar_nivel(stub, access_level):
    print()
    print("=" * 70)
    print(f"TESTANDO NÍVEL: {access_level}")
    print("=" * 70)

    requisicao = patient_pb2.SinglePatientRequest(
        patient_id=PATIENT_ID,
        access_level=access_level
    )

    resposta = stub.GetSinglePatientData(
        requisicao,
        timeout=30
    )

    if not resposta.raw_database_json:
        raise RuntimeError(
            "O Patient Data retornou raw_database_json vazio."
        )

    try:
        bundle = json.loads(
            resposta.raw_database_json
        )

    except json.JSONDecodeError as erro:
        raise RuntimeError(
            "O Patient Data não retornou um JSON válido."
        ) from erro

    if bundle.get("resourceType") != "Bundle":
        print(
            json.dumps(
                bundle,
                indent=2,
                ensure_ascii=False
            )
        )

        raise RuntimeError(
            "A resposta não é um Bundle FHIR. "
            "O Patient Data pode ainda estar devolvendo o JSON bruto."
        )

    tipos = imprimir_resumo(bundle)

    pacientes = encontrar_recursos(
        bundle,
        "Patient"
    )

    if len(pacientes) != 1:
        raise RuntimeError(
            "Era esperado exatamente um recurso Patient, "
            f"mas foram encontrados {len(pacientes)}."
        )

    patient = pacientes[0]
    erros = []

    erros.extend(
        validar_identidade(
            patient,
            access_level
        )
    )

    erros.extend(
        validar_referencias(
            bundle,
            patient.get("id")
        )
    )

    if tipos.get("Encounter", 0) == 0:
        erros.append(
            "Nenhum Encounter foi retornado."
        )

    quantidade_eventos = (
        tipos.get("Condition", 0)
        + tipos.get("Observation", 0)
        + tipos.get("MedicationRequest", 0)
    )

    if quantidade_eventos == 0:
        erros.append(
            "Nenhum evento clínico foi convertido."
        )

    if bundle.get("total") != len(bundle.get("entry", [])):
        erros.append(
            "O campo total não corresponde ao número de entries."
        )

    if erros:
        print("\nFALHAS ENCONTRADAS:")

        for erro in erros:
            print(f"  - {erro}")

        return False

    print("\nSUCESSO:")
    print(
        f"  Patient Data consultou o paciente {PATIENT_ID}, "
        "chamou o Data Transform e recebeu um Bundle FHIR."
    )

    print(
        f"  Política {access_level} aplicada corretamente."
    )

    return True


def main():
    print("Teste de integração:")
    print(
        "PostgreSQL → Patient Data → Data Transform → resposta FHIR"
    )

    channel = grpc.insecure_channel(
        PATIENT_DATA_ADDRESS
    )

    try:
        grpc.channel_ready_future(
            channel
        ).result(timeout=5)

    except grpc.FutureTimeoutError:
        print(
            "\nERRO: não foi possível conectar ao Patient Data em "
            f"{PATIENT_DATA_ADDRESS}."
        )

        print(
            "Confirme se patientdata/main.py está em execução."
        )

        return 1

    stub = patient_pb2_grpc.PatientDataServiceStub(
        channel
    )

    resultados = []

    try:
        for access_level in ACCESS_LEVELS:
            resultado = testar_nivel(
                stub,
                access_level
            )

            resultados.append(
                (access_level, resultado)
            )

    except grpc.RpcError as erro:
        print("\nERRO gRPC:")
        print("  Código:", erro.code())
        print("  Detalhes:", erro.details())

        return 1

    except Exception as erro:
        print("\nERRO NO TESTE:")
        print(
            f"  {type(erro).__name__}: {erro}"
        )

        return 1

    finally:
        channel.close()

    print()
    print("=" * 70)
    print("RESULTADO FINAL")
    print("=" * 70)

    sucesso_total = True

    for access_level, sucesso in resultados:
        estado = "PASSOU" if sucesso else "FALHOU"
        print(f"  {access_level}: {estado}")

        if not sucesso:
            sucesso_total = False

    if sucesso_total:
        print(
            "\nTodos os testes de integração passaram."
        )

        return 0

    print(
        "\nUm ou mais níveis apresentaram falhas."
    )

    return 1


if __name__ == "__main__":
    raise SystemExit(main())