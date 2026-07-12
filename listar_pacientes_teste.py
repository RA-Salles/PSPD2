import os
import psycopg2


with psycopg2.connect(
    host=os.getenv("DB_HOST", "localhost"),
    port=int(os.getenv("DB_PORT", "5433")),
    database=os.getenv("DB_NAME", "pseudopep_g02"),
    user=os.getenv("DB_USER", "grupo02_user"),
    password=os.getenv("DB_PASS", "123@g02"),
    connect_timeout=10
) as conexao:

    with conexao.cursor() as cursor:
        cursor.execute("""
            SELECT
                p.patient_id,
                p.full_name,
                COUNT(DISTINCT e.encounter_id) AS atendimentos,
                COUNT(DISTINCT c.event_id) AS eventos
            FROM patients p
            LEFT JOIN encounters e
              ON e.patient_id = p.patient_id
            LEFT JOIN clinical_events c
              ON c.patient_id = p.patient_id
            GROUP BY p.patient_id, p.full_name
            HAVING COUNT(DISTINCT e.encounter_id) > 0
               AND COUNT(DISTINCT c.event_id) > 0
            ORDER BY eventos DESC
            LIMIT 10
        """)

        print(
            "ID | Nome | Atendimentos | Eventos"
        )

        for paciente in cursor.fetchall():
            print(
                f"{paciente[0]} | "
                f"{paciente[1]} | "
                f"{paciente[2]} | "
                f"{paciente[3]}"
            )