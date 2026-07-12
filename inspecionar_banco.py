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
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)

        tabelas = [linha[0] for linha in cursor.fetchall()]

        print("Tabelas encontradas:")

        for tabela in tabelas:
            print(f"\n[{tabela}]")

            cursor.execute("""
                SELECT column_name, data_type
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = %s
                ORDER BY ordinal_position
            """, (tabela,))

            for coluna, tipo in cursor.fetchall():
                print(f"  {coluna}: {tipo}")