"""Políticas de acesso e conversão dos registros do PEP para HL7/FHIR R4."""

from __future__ import annotations

import hashlib
import hmac
import re
from collections import Counter
from datetime import date, datetime
from statistics import mean, median
from typing import Any, Iterable

import transform_pb2
import transform_pb2_grpc


VALID_ACCESS_LEVELS = {"FULL", "PARTIAL", "ANONYMIZED", "AGGREGATED"}


class TransformError(ValueError):
    """Erro de entrada que deve ser apresentado como INVALID_ARGUMENT."""


def _first(data: dict[str, Any], *names: str, default: Any = None) -> Any:
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return default


def _iso(value: Any) -> str | None:
    if value in (None, ""):
        return None
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def _gender(value: Any) -> str:
    normalized = str(value or "unknown").strip().lower()
    return {
        "m": "male", "masculino": "male", "male": "male",
        "f": "female", "feminino": "female", "female": "female",
        "o": "other", "outro": "other", "other": "other",
    }.get(normalized, "unknown")


def _initials(name: str) -> str:
    return " ".join(f"{word[0].upper()}." for word in name.split() if word)


def _birth_year(value: Any) -> int | None:
    if not value:
        return None
    match = re.match(r"^(\d{4})", str(value))
    return int(match.group(1)) if match else None


def _age_group(value: Any) -> str | None:
    year = _birth_year(value)
    if year is None:
        return None
    age = max(0, date.today().year - year)
    if age < 18:
        return "0-17"
    if age < 40:
        return "18-39"
    if age < 60:
        return "40-59"
    return "60+"


def _pseudo(real_id: Any, secret: str) -> str:
    digest = hmac.new(secret.encode(), str(real_id).encode(), hashlib.sha256).hexdigest()
    return f"anon-{digest[:16]}"


def _reference_id(real_id: Any, level: str, secret: str) -> str:
    return _pseudo(real_id, secret) if level == "ANONYMIZED" else str(real_id)


def _patient_resource(row: dict[str, Any], level: str, secret: str) -> dict[str, Any]:
    real_id = _first(row, "id_paciente", "patient_id", "id")
    if real_id is None:
        raise TransformError("Registro de paciente sem id_paciente")
    name = str(_first(row, "nome", "full_name", "name", default=""))
    birth = _first(row, "data_nascimento", "data de nascimento", "birth_date", "birthDate")
    resource: dict[str, Any] = {
        "resourceType": "Patient",
        "id": _reference_id(real_id, level, secret),
        "gender": _gender(_first(row, "genero", "gênero", "sexo", "gender")),
    }

    if level == "FULL":
        if name:
            resource["name"] = [{"text": name}]
        if birth:
            resource["birthDate"] = str(birth)[:10]
        identifiers = []
        cpf = _first(row, "cpf")
        cns = _first(row, "cns", "numero_cns", "número do CNS")
        if cpf:
            identifiers.append({"system": "urn:br:cpf", "value": str(cpf)})
        if cns:
            identifiers.append({"system": "urn:br:cns", "value": str(cns)})
        if identifiers:
            resource["identifier"] = identifiers
        city, state = _first(row, "cidade", "city"), _first(row, "estado", "state")
        if city or state:
            resource["address"] = [{"city": city, "state": state}]
    elif level == "PARTIAL":
        if name:
            resource["name"] = [{"text": _initials(name)}]
        year = _birth_year(birth)
        if year:
            resource["extension"] = [{
                "url": "https://example.org/fhir/StructureDefinition/birth-year",
                "valueInteger": year,
            }]
        city, state = _first(row, "cidade", "city"), _first(row, "estado", "state")
        if city or state:
            resource["address"] = [{"city": city, "state": state}]
    else:  # ANONYMIZED
        group = _age_group(birth)
        state = _first(row, "estado", "state")
        extensions = []
        if group:
            extensions.append({
                "url": "https://example.org/fhir/StructureDefinition/age-group",
                "valueString": group,
            })
        if extensions:
            resource["extension"] = extensions
        if state:
            resource["address"] = [{"state": state}]
    return resource


def _encounter_resource(row: dict[str, Any], level: str, secret: str) -> dict[str, Any]:
    patient_id = _first(row, "id_paciente", "patient_id")
    encounter_id = _first(row, "id_atendimento", "encounter_id", "id")
    resource: dict[str, Any] = {
        "resourceType": "Encounter",
        "id": str(encounter_id),
        "status": "finished" if _first(row, "data_fim", "end_date") else "in-progress",
        "class": {
            "system": "http://terminology.hl7.org/CodeSystem/v3-ActCode",
            "code": "AMB",
            "display": str(_first(row, "tipo_atendimento", "tipo de atendimento", "encounter_type", default="Atendimento")),
        },
        "subject": {"reference": f"Patient/{_reference_id(patient_id, level, secret)}"},
    }
    start, end = _first(row, "data_inicio", "start_date"), _first(row, "data_fim", "end_date")
    if start or end:
        resource["period"] = {k: v for k, v in {"start": _iso(start), "end": _iso(end)}.items() if v}
    sector = _first(row, "setor", "departamento", "department")
    if sector:
        resource["serviceType"] = {"text": str(sector)}
    return resource


def _event_resource(row: dict[str, Any], level: str, secret: str) -> dict[str, Any]:
    event_type = str(_first(row, "tipo_evento", "tipo do evento", "event_type", default="")).lower()
    patient_id = _first(row, "id_paciente", "patient_id")
    event_id = _first(row, "id_evento", "event_id", "id")
    code = _first(row, "codigo_tipo_evento", "código do tipo de evento", "event_code", "code")
    description = _first(row, "descricao_evento", "descrição do evento", "description", default=code)
    occurred = _first(row, "data_evento", "event_date", "date")
    subject = {"reference": f"Patient/{_reference_id(patient_id, level, secret)}"}
    coding = {"text": str(description or code or "Evento clínico")}
    if code:
        coding["coding"] = [{"system": "urn:hospital:clinical-event", "code": str(code), "display": str(description or code)}]

    if any(term in event_type for term in ("cond", "diagn")):
        resource: dict[str, Any] = {
            "resourceType": "Condition", "id": str(event_id),
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": coding, "subject": subject,
        }
        if occurred:
            resource["recordedDate"] = _iso(occurred)
        return resource

    if any(term in event_type for term in ("observ", "exam", "labor")):
        resource = {
            "resourceType": "Observation", "id": str(event_id), "status": "final",
            "code": coding, "subject": subject,
        }
        if occurred:
            resource["effectiveDateTime"] = _iso(occurred)
        value, unit = _first(row, "valor", "value"), _first(row, "unidade", "unidade_valor", "unit")
        if value is not None:
            try:
                resource["valueQuantity"] = {"value": float(value), **({"unit": str(unit)} if unit else {})}
            except (TypeError, ValueError):
                resource["valueString"] = str(value)
        return resource

    if any(term in event_type for term in ("med", "prescri")):
        resource = {
            "resourceType": "MedicationRequest", "id": str(event_id), "status": "active",
            "intent": "order", "medicationCodeableConcept": coding, "subject": subject,
        }
        if occurred:
            resource["authoredOn"] = _iso(occurred)
        value, unit = _first(row, "valor", "value"), _first(row, "unidade", "unidade_valor", "unit")
        if value is not None or unit:
            resource["dosageInstruction"] = [{"text": " ".join(str(x) for x in (value, unit) if x is not None)}]
        return resource

    raise TransformError(f"Tipo de evento clínico desconhecido: {event_type or '<vazio>'}")


def _as_list(value: Any) -> list[dict[str, Any]]:
    if value is None:
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list) and all(isinstance(item, dict) for item in value):
        return value
    raise TransformError("Coleção de registros possui formato inválido")


def _extract(payload: Any) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    if isinstance(payload, list):
        return payload, [], []
    if not isinstance(payload, dict):
        raise TransformError("raw_database_json deve conter um objeto ou uma lista JSON")
    # Formato unitário e formato de lote emitidos pelo Patient Data atual.
    if "lote_coorte" in payload:
        patients = _as_list(payload["lote_coorte"])
    else:
        patients = _as_list(_first(payload, "paciente", "patients", "patient"))
    encounters = _as_list(_first(payload, "atendimentos", "encounters"))
    events = _as_list(_first(payload, "eventos_clinicos", "clinical_events", "events"))
    return patients, encounters, events


def _percentages(values: Iterable[str]) -> dict[str, float]:
    counter = Counter(values)
    total = sum(counter.values())
    return {key: round(value * 100 / total, 2) for key, value in sorted(counter.items())} if total else {}


def _aggregate(patients: list[dict[str, Any]], events: list[dict[str, Any]]) -> dict[str, Any]:
    numeric_values: list[float] = []
    medications: list[str] = []
    for event in events:
        event_type = str(_first(event, "tipo_evento", "event_type", default="")).lower()
        if "observ" in event_type or "exam" in event_type:
            try:
                numeric_values.append(float(_first(event, "valor", "value")))
            except (TypeError, ValueError):
                pass
        if "med" in event_type:
            medications.append(str(_first(event, "codigo_tipo_evento", "event_code", "code", default="desconhecido")))
    summary: dict[str, Any] = {
        "resourceType": "Parameters",
        "parameter": [
            {"name": "total-patients", "valueInteger": len(patients)},
            {"name": "gender-distribution-percent", "valueString": str(_percentages(_gender(_first(p, "genero", "gênero", "sexo", "gender")) for p in patients))},
            {"name": "age-group-distribution-percent", "valueString": str(_percentages(filter(None, (_age_group(_first(p, "data_nascimento", "birth_date")) for p in patients))))},
            {"name": "medication-frequency", "valueString": str(dict(Counter(medications).most_common()))},
        ],
    }
    if numeric_values:
        summary["parameter"].extend([
            {"name": "numeric-observation-mean", "valueDecimal": mean(numeric_values)},
            {"name": "numeric-observation-median", "valueDecimal": median(numeric_values)},
        ])
    return summary


def transform_payload(payload: Any, access_level: str, pseudonym_secret: str) -> dict[str, Any]:
    """Transforma o JSON bruto em Bundle FHIR ou Parameters agregado."""
    level = str(access_level or "").upper()
    if level not in VALID_ACCESS_LEVELS:
        raise TransformError(f"Nível de acesso inválido: {access_level!r}")
    patients, encounters, events = _extract(payload)
    if level == "AGGREGATED":
        return _aggregate(patients, events)

    entries = []
    for row in patients:
        entries.append({"resource": _patient_resource(row, level, pseudonym_secret)})
    for row in encounters:
        entries.append({"resource": _encounter_resource(row, level, pseudonym_secret)})
    for row in events:
        entries.append({"resource": _event_resource(row, level, pseudonym_secret)})
    return {
        "resourceType": "Bundle",
        "type": "collection",
        "total": len(entries),
        "entry": entries,
    }
