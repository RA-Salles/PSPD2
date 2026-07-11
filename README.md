# PSPD2
Projeto para adaptar aplicação em banco de dados médicos para arquitetura em microsserviços

## MISC: Executar o teste_data_transform:
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
python teste_data_transform
```
