import unittest

from transformer import TransformError, transform_payload


PAYLOAD = {
    "paciente": {
        "id_paciente": "P000001", "nome": "João da Silva",
        "data_nascimento": "1970-05-10", "genero": "M",
        "cidade": "Brasília", "estado": "DF", "cpf": "00000000000", "cns": "123",
    },
    "eventos_clinicos": [{
        "id_evento": "EV1", "id_paciente": "P000001", "tipo_evento": "Observação",
        "codigo_tipo_evento": "GLICOSE", "descricao_evento": "Glicemia",
        "data_evento": "2026-01-10", "valor": "182", "unidade": "mg/dL",
    }],
}


class TransformerTests(unittest.TestCase):
    def test_full_preserves_identity(self):
        result = transform_payload(PAYLOAD, "FULL", "secret")
        patient = result["entry"][0]["resource"]
        self.assertEqual(patient["id"], "P000001")
        self.assertEqual(patient["name"][0]["text"], "João da Silva")
        self.assertIn("identifier", patient)

    def test_partial_removes_direct_identifiers(self):
        patient = transform_payload(PAYLOAD, "PARTIAL", "secret")["entry"][0]["resource"]
        self.assertEqual(patient["name"][0]["text"], "J. D. S.")
        self.assertNotIn("identifier", patient)
        self.assertNotIn("birthDate", patient)

    def test_anonymized_replaces_real_id(self):
        result = transform_payload(PAYLOAD, "ANONYMIZED", "secret")
        patient = result["entry"][0]["resource"]
        observation = result["entry"][1]["resource"]
        self.assertTrue(patient["id"].startswith("anon-"))
        self.assertNotIn("name", patient)
        self.assertNotIn("P000001", observation["subject"]["reference"])

    def test_invalid_level(self):
        with self.assertRaises(TransformError):
            transform_payload(PAYLOAD, "DENY", "secret")


if __name__ == "__main__":
    unittest.main()
