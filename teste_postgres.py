import os
import psycopg2


config = {
    "host": os.getenv("DB_HOST", "localhost"),
    "port": int(os.getenv("DB_PORT", "5433")),
    "database": os.getenv("DB_NAME", "pseudopep_g02"),
    "user": os.getenv("DB_USER", "grupo02_user"),
    "password": os.getenv("DB_PASS", "123@g02"),
    "connect_timeout": 10
}

try:
    with psycopg2.connect(**config) as conexao:
        with conexao.cursor() as cursor:
            cursor.execute(
                "SELECT current_database(), current_user, version()"
            )

            banco, usuario, versao = cursor.fetchone()

            print("Conexão realizada!")
            print("Banco:", banco)
            print("Usuário:", usuario)
            print("PostgreSQL:", versao)

except Exception as erro:
    print("Falha ao conectar:")
    print(type(erro).__name__, erro)