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
# Implantação Docker e Kubernetes 

Execute os comandos a partir da raiz do projeto no PowerShell. <br>
Usuários e Senhas:

1. **med.cardoso** <br>
**PseudoPEP2026!** <br>
<br>

2. **pes.mendes** <br>
**PseudoPEP2026!** <br>


## 1. Teste local com Docker Compose

Mantenha o túnel SSH do PostgreSQL aberto em outro terminal:

```powershell
ssh -N -o ExitOnForwardFailure=yes -L 5433:192.168.122.1:5432 -p 10200 aSUA_MATRICULA@kiriland.unb.br
```

Crie o arquivo local `.env` (ele não deve ser enviado ao Git):

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha `DB_PASS` e `PSEUDONYM_SECRET`, então execute:

```powershell
docker compose config
docker compose up --build -d
docker compose ps
docker compose logs -f
```

A aplicação local estará em `http://localhost:3000`. Para encerrar:

```powershell
docker compose down
```

## 2. Publicar as imagens no Docker Hub

Depois que o teste local passar:

```powershell
docker compose build
docker compose push
```

Confirme que as cinco imagens aparecem em `docker.io/orlandirodrigo` com a tag `v1`.

## 3. Validar o acesso ao cluster

```powershell
$KUBECONFIG = ".\docs\kubeconfig-grupo-2.yaml"
kubectl get pods --kubeconfig=$KUBECONFIG
kubectl get resourcequota --kubeconfig=$KUBECONFIG
```

O kubeconfig já seleciona o namespace `grupo-2`.

## 4. Criar os segredos no namespace

O segredo não é armazenado nos YAMLs:

```powershell
kubectl create secret generic pspd2-secrets `
  --namespace=grupo-2 `
  --from-literal=db-password="SENHA_DO_POSTGRES" `
  --from-literal=pseudonym-secret="SEGREDO_LONGO_ALEATORIO" `
  --from-literal=flask-secret="OUTRO_SEGREDO_LONGO_ALEATORIO" `
  --kubeconfig=$KUBECONFIG
```

Para recriá-lo, apague primeiro com `kubectl delete secret pspd2-secrets ...`.

## 5. Implantar uma réplica de cada componente

Não aplique o HPA na primeira validação:

```powershell
kubectl apply -f .\k8s\configmap.yaml --kubeconfig=$KUBECONFIG
kubectl apply -f .\k8s\auth.yaml --kubeconfig=$KUBECONFIG
kubectl apply -f .\k8s\data-transform.yaml --kubeconfig=$KUBECONFIG
kubectl apply -f .\k8s\patient-data.yaml --kubeconfig=$KUBECONFIG
kubectl apply -f .\k8s\gateway.yaml --kubeconfig=$KUBECONFIG
kubectl apply -f .\k8s\frontend.yaml --kubeconfig=$KUBECONFIG
kubectl apply -f .\k8s\ingress.yaml --kubeconfig=$KUBECONFIG
```

Acompanhe:

```powershell
kubectl get pods -w --kubeconfig=$KUBECONFIG
kubectl get services,ingress --kubeconfig=$KUBECONFIG
```

## 6. Diagnóstico

```powershell
kubectl logs deployment/api-gateway --kubeconfig=$KUBECONFIG
kubectl logs deployment/auth --kubeconfig=$KUBECONFIG
kubectl logs deployment/patient-data --kubeconfig=$KUBECONFIG
kubectl logs deployment/data-transform --kubeconfig=$KUBECONFIG
kubectl describe pod NOME_DO_POD --kubeconfig=$KUBECONFIG
```

Teste primeiro o Gateway sem Ingress:

```powershell
kubectl port-forward service/api-gateway 5000:80 --kubeconfig=$KUBECONFIG
```

Em outro terminal:

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/api/public
```

Depois acesse `https://kiriland.unb.br/grupo2`.

## 7. HPA

Somente após a validação funcional:

```powershell
kubectl apply -f .\k8s\hpa.yaml --kubeconfig=$KUBECONFIG
kubectl get hpa -w --kubeconfig=$KUBECONFIG
```

O HPA depende do Metrics Server do cluster e dos `resources.requests` configurados nos Deployments.

## 8. Atualizações posteriores

Use uma nova tag, por exemplo `v2`, altere as imagens em `docker-compose.yml` e `k8s/*.yaml`, depois:

```powershell
docker compose build
docker compose push
kubectl apply -f .\k8s --kubeconfig=$KUBECONFIG
```

Evite reutilizar a mesma tag durante os experimentos; tags distintas tornam cada cenário reproduzível.
