# PSPD2
Projeto para adaptar aplicação em banco de dados médicos para arquitetura em microsserviços

## Variáveis do Banco - Grupo 02
Caso seja necessário colocar no terminal Powershell:
```
$env:DB_HOST = "localhost"
$env:DB_PORT = "5433"
$env:DB_NAME = "pseudopep_g02"
$env:DB_USER = "grupo02_user"
$env:DB_PASS = "123@g02"
```

# Execução de Testes
## I. Executar o teste_data_transform.py:
1. Na pasta pspd2:
```
pip install -m requirements.txt
```
2. Abra 4 terminais para cada parte do serviço e os execute
```
cd auth
python main.py
```

```
cd datatransf
python main.py
```

```
cd patientdata
python main.py
```

```
cd gateway
python app.py
```

3. Execute o arquivo teste em um quinto terminal:
```
python teste_data_transform.py
```

## II. Executar o teste_postgres.py:
1. Na pasta pspd2:
```
pip install -m requirements.txt
```
2. Abra um terminal para estabelecer conexão com o servidor, troque a matrícula para a sua e digite a senha corretamente:
```
ssh -v -N `
  -o ExitOnForwardFailure=yes `
  -L 5433:192.168.122.1:5432 `
  -p 10200 `
  a<Sua matrícula>@kiriland.unb.br
```

3. Abra outro terminal e execute o código:
```
python teste_postgres.py
```
