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
            SELECT event_type, COUNT(*)
            FROM clinical_events
            GROUP BY event_type
            ORDER BY event_type
        """)

        print("Tipos de eventos:")

        for tipo, quantidade in cursor.fetchall():
            print(f"  {tipo}: {quantidade}")

        cursor.execute("""
            SELECT code, description, COUNT(*)
            FROM clinical_events
            GROUP BY code, description
            ORDER BY code
            LIMIT 30
        """)

        print("\nAlguns códigos clínicos:")

        for codigo, descricao, quantidade in cursor.fetchall():
            print(
                f"  {codigo}: {descricao} "
                f"({quantidade} registros)"
            )