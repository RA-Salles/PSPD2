import jwt
import datetime

# mesma chave que no auth/main.py
SECRET_KEY = "PSPD2SecretKey"

def gerar_token_teste(cargo):
    payload = {
        "sub": "usuario_teste@hospital.com",
        "cargo": cargo,                     
        "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)
    }
    
    token = jwt.encode(payload, SECRET_KEY, algorithm="HS256")
    return token

if __name__ == "__main__":
    print("--- Gerador de token para testes ---")
    
    token_medico = gerar_token_teste(cargo="medico")
    print(f"\nToken de MÉDICO (tem que retornar FULL em ResumoClinico):")
    print(token_medico)
    
    token_pesquisador = gerar_token_teste(cargo="pesquisador")
    print(f"\nToken de PESQUISADOR (tem que retornar ANONYMIZED em ResumoCoorte):")
    print(token_pesquisador)