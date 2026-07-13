# PSPD2
Projeto para adaptar aplicação em banco de dados médicos para arquitetura em microsserviços

## Link para a apresentação:
https://youtu.be/SSx7qNZbL8I

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

## IMPORTANTE: Para terminal rodar corretamente:
```
$KUBECONFIG = (
    Resolve-Path .\docs\kubeconfig-grupo-2.yaml
).Path
```

Execute os comandos a partir da raiz do projeto no PowerShell. <br>
Usuários e Senhas:

1. **med.cardoso** <br>
**PseudoPEP2026!** <br>
<br>

2. **pes.mendes** <br>
**PseudoPEP2026!** <br>


## 1. Pré-requisitos

Para executar a aplicação localmente com Docker:

- Docker Desktop instalado e em execução;
- acesso SSH ao servidor Kiriland;
- arquivo `.env.example` disponível na raiz do projeto;
- porta local `5433` disponível.

Para realizar a implantação no Kubernetes:

- `kubectl` instalado;
- arquivo `docs/kubeconfig-grupo-2.yaml`;
- acesso ao namespace `grupo-2`;
- imagens disponíveis no Docker Hub.

As imagens do grupo estão publicadas em:

```text
orlandirodrigo/pspd2-frontend:v1
orlandirodrigo/pspd2-gateway:v1
orlandirodrigo/pspd2-auth:v1
orlandirodrigo/pspd2-patient-data:v1
orlandirodrigo/pspd2-data-transform:v1
```

## 2. Usuários para validação funcional

Os usuários de teste são fornecidos pelo professor.

Exemplos:

```text
Médico: med.cardoso
Pesquisador: pes.mendes
```

As senhas não devem ser armazenadas no README, no código-fonte, nos Dockerfiles ou nos manifestos Kubernetes.

## 3. Abrir o túnel SSH do PostgreSQL

O PostgreSQL da disciplina não está diretamente acessível pelo computador local. Antes de iniciar os contêineres, abra um túnel SSH.

Em um PowerShell separado, substitua `SUA_MATRICULA` e execute:

```powershell
ssh -N `
  -o ExitOnForwardFailure=yes `
  -L 5433:192.168.122.1:5432 `
  -p 10200 `
  aSUA_MATRICULA@kiriland.unb.br
```

Depois da autenticação, o terminal permanecerá aparentemente parado. Isso é normal e indica que o túnel está ativo.

Mantenha esse terminal aberto durante toda a execução local.

Para confirmar o funcionamento do túnel, abra outro PowerShell:

```powershell
Test-NetConnection localhost -Port 5433
```

O resultado esperado é:

```text
TcpTestSucceeded : True
```

## 4. Configurar as variáveis locais

Na raiz do projeto, crie o arquivo `.env`:

```powershell
Copy-Item .env.example .env
notepad .env
```

Preencha as variáveis:

```env
DB_PASS=SENHA_DO_POSTGRES
PSEUDONYM_SECRET=SEGREDO_LONGO_E_ALEATORIO
```

O arquivo `.env` contém informações sensíveis e não deve ser enviado ao Git.

## 5. Executar usando imagens prontas

Quem deseja apenas executar a aplicação pode baixar as imagens já publicadas:

```powershell
docker compose pull
```

Depois, inicie os contêineres sem reconstruir as imagens:

```powershell
docker compose up -d --no-build
```

Confira o estado:

```powershell
docker compose ps
```

Os cinco serviços devem aparecer como ativos:

```text
frontend
gateway
auth
patient-data
data-transform
```

Para acompanhar os logs:

```powershell
docker compose logs -f
```

O comando permanecerá acompanhando os logs. Pressione `Ctrl + C` para encerrar o acompanhamento sem desligar os contêineres.

Acesse a aplicação em:

```text
http://localhost:3000/grupo2/
```

Verifique os endpoints de saúde:

```powershell
Invoke-WebRequest http://localhost:3000/health
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/api/public
```

## 6. Construir as imagens localmente

Para construir a aplicação a partir do código-fonte:

```powershell
docker compose build
docker compose up -d
```

Para reconstruir completamente, ignorando o cache:

```powershell
docker compose build --no-cache
docker compose up -d
```

Confira os contêineres:

```powershell
docker compose ps
```

Para encerrar a aplicação:

```powershell
docker compose down
```

Para encerrar e remover também volumes associados:

```powershell
docker compose down --volumes
```

## 7. Publicar as imagens no Docker Hub

Esta etapa deve ser executada somente pelo responsável pela publicação das imagens.

Autentique-se no Docker Hub:

```powershell
docker login
```

Construa as imagens:

```powershell
docker compose build
```

Publique:

```powershell
docker compose push
```

Confirme as imagens locais:

```powershell
docker image ls "orlandirodrigo/pspd2-*"
```

Antes da publicação, confirme que nenhuma senha está gravada:

- no código-fonte;
- nos Dockerfiles;
- no `docker-compose.yml`;
- nas imagens;
- nos arquivos versionados pelo Git.

## 8. Configurar o acesso ao Kubernetes

Defina o caminho do kubeconfig:

```powershell
$KUBECONFIG = ".\docs\kubeconfig-grupo-2.yaml"
```

Valide o acesso ao cluster:

```powershell
kubectl get pods --kubeconfig=$KUBECONFIG
kubectl get resourcequota --kubeconfig=$KUBECONFIG
```

O arquivo já utiliza o namespace:

```text
grupo-2
```

Para confirmar o contexto:

```powershell
kubectl config view `
  --minify `
  --kubeconfig=$KUBECONFIG
```

## 9. Criar os Secrets do Kubernetes

As informações sensíveis não são armazenadas nos manifestos YAML.

Confira se o Secret já existe:

```powershell
kubectl get secret pspd2-secrets `
  --namespace=grupo-2 `
  --kubeconfig=$KUBECONFIG
```

Caso não exista, crie-o:

```powershell
kubectl create secret generic pspd2-secrets `
  --namespace=grupo-2 `
  --from-literal=db-password="SENHA_DO_POSTGRES" `
  --from-literal=pseudonym-secret="SEGREDO_LONGO_ALEATORIO" `
  --from-literal=flask-secret="OUTRO_SEGREDO_LONGO_ALEATORIO" `
  --kubeconfig=$KUBECONFIG
```

Para recriar o Secret, remova o anterior:

```powershell
kubectl delete secret pspd2-secrets `
  --namespace=grupo-2 `
  --kubeconfig=$KUBECONFIG
```

Depois execute novamente o comando de criação.

## 10. Implantar uma réplica de cada componente

Na primeira validação funcional, não aplique o HPA.

Aplique o ConfigMap:

```powershell
kubectl apply -f .\k8s\configmap.yaml `
  --kubeconfig=$KUBECONFIG
```

Aplique o Authorization Service:

```powershell
kubectl apply -f .\k8s\auth.yaml `
  --kubeconfig=$KUBECONFIG
```

Aplique o Data Transform:

```powershell
kubectl apply -f .\k8s\data-transform.yaml `
  --kubeconfig=$KUBECONFIG
```

Aplique o Patient Data:

```powershell
kubectl apply -f .\k8s\patient-data.yaml `
  --kubeconfig=$KUBECONFIG
```

Aplique a API Gateway:

```powershell
kubectl apply -f .\k8s\gateway.yaml `
  --kubeconfig=$KUBECONFIG
```

Aplique o frontend:

```powershell
kubectl apply -f .\k8s\frontend.yaml `
  --kubeconfig=$KUBECONFIG
```

Aplique o Ingress:

```powershell
kubectl apply -f .\k8s\ingress.yaml `
  --kubeconfig=$KUBECONFIG
```

## 11. Acompanhar os pods

Para acompanhar continuamente:

```powershell
kubectl get pods -w --kubeconfig=$KUBECONFIG
```

A opção `-w` significa `--watch`. Portanto, o terminal permanece acompanhando alterações no estado dos pods.

Quando todos estiverem `Running` e `Ready`, pressione:

```text
Ctrl + C
```

Isso encerra apenas o acompanhamento. Os pods continuam em execução.

Para fazer uma consulta pontual:

```powershell
kubectl get pods --kubeconfig=$KUBECONFIG
```

Confira os demais recursos:

```powershell
kubectl get deployments --kubeconfig=$KUBECONFIG
kubectl get services --kubeconfig=$KUBECONFIG
kubectl get ingress --kubeconfig=$KUBECONFIG
```

## 12. Validar os serviços antes do Ingress

Teste primeiro a API Gateway com redirecionamento local:

```powershell
kubectl port-forward service/api-gateway 5000:80 `
  --kubeconfig=$KUBECONFIG
```

O comando permanecerá aberto enquanto o redirecionamento estiver ativo.

Em outro PowerShell:

```powershell
Invoke-RestMethod http://localhost:5000/health
Invoke-RestMethod http://localhost:5000/api/public
```

Teste também o frontend:

```powershell
kubectl port-forward service/frontend 8080:80 `
  --kubeconfig=$KUBECONFIG
```

Acesse:

```text
http://localhost:8080/grupo2/
```

Se o Gateway e o frontend funcionarem com `port-forward`, mas o endereço público não funcionar, o problema estará no Ingress, e não nas imagens ou nos pods.

## 13. Validar o Ingress

Confira os recursos:

```powershell
kubectl get ingress -o wide `
  --kubeconfig=$KUBECONFIG
```

Inspecione as regras da API:

```powershell
kubectl describe ingress pspd2-api `
  --kubeconfig=$KUBECONFIG
```

Inspecione as regras do frontend:

```powershell
kubectl describe ingress pspd2-frontend `
  --kubeconfig=$KUBECONFIG
```

Confira os endpoints:

```powershell
kubectl get endpoints frontend `
  --kubeconfig=$KUBECONFIG

kubectl get endpoints api-gateway `
  --kubeconfig=$KUBECONFIG
```

Os endpoints não devem aparecer como:

```text
<none>
```

Depois, acesse:

```text
https://kiriland.unb.br/grupo2/
```

## 14. Diagnóstico

### Logs da API Gateway

```powershell
kubectl logs deployment/api-gateway `
  --kubeconfig=$KUBECONFIG
```

### Logs do Authorization Service

```powershell
kubectl logs deployment/auth `
  --kubeconfig=$KUBECONFIG
```

### Logs do Patient Data

```powershell
kubectl logs deployment/patient-data `
  --kubeconfig=$KUBECONFIG
```

### Logs do Data Transform

```powershell
kubectl logs deployment/data-transform `
  --kubeconfig=$KUBECONFIG
```

### Logs do frontend

```powershell
kubectl logs deployment/frontend `
  --kubeconfig=$KUBECONFIG
```

Para acompanhar continuamente:

```powershell
kubectl logs -f deployment/api-gateway `
  --kubeconfig=$KUBECONFIG
```

Para inspecionar um pod:

```powershell
kubectl describe pod NOME_DO_POD `
  --kubeconfig=$KUBECONFIG
```

Para consultar os eventos recentes:

```powershell
kubectl get events `
  --sort-by=.metadata.creationTimestamp `
  --kubeconfig=$KUBECONFIG
```

## 15. Escalabilidade horizontal manual

Antes de ativar o HPA, podem ser realizados testes com quantidades fixas de réplicas.

### Uma réplica

```powershell
kubectl scale deployment/api-gateway --replicas=1 `
  --kubeconfig=$KUBECONFIG

kubectl scale deployment/auth --replicas=1 `
  --kubeconfig=$KUBECONFIG

kubectl scale deployment/patient-data --replicas=1 `
  --kubeconfig=$KUBECONFIG

kubectl scale deployment/data-transform --replicas=1 `
  --kubeconfig=$KUBECONFIG
```

### Três réplicas

```powershell
kubectl scale deployment/api-gateway --replicas=3 `
  --kubeconfig=$KUBECONFIG

kubectl scale deployment/auth --replicas=3 `
  --kubeconfig=$KUBECONFIG

kubectl scale deployment/patient-data --replicas=3 `
  --kubeconfig=$KUBECONFIG

kubectl scale deployment/data-transform --replicas=3 `
  --kubeconfig=$KUBECONFIG
```

Confira a distribuição dos pods entre os nós:

```powershell
kubectl get pods -o wide `
  --kubeconfig=$KUBECONFIG
```

## 16. Ativar o HPA

Aplique o HPA somente depois que a validação funcional for concluída:

```powershell
kubectl apply -f .\k8s\hpa.yaml `
  --kubeconfig=$KUBECONFIG
```

Acompanhe:

```powershell
kubectl get hpa -w `
  --kubeconfig=$KUBECONFIG
```

Novamente, a opção `-w` mantém o terminal acompanhando alterações. Pressione `Ctrl + C` para sair.

Confira se as métricas de CPU estão disponíveis:

```powershell
kubectl top pods `
  --kubeconfig=$KUBECONFIG
```

Se a coluna `TARGETS` do HPA apresentar `<unknown>`, verifique se o Metrics Server do cluster está funcionando.

## 17. Atualizar a aplicação

Para uma atualização posterior, utilize uma nova tag, como `v2`.

Atualize os nomes das imagens:

- no `docker-compose.yml`;
- nos arquivos `k8s/*.yaml`.

Depois, construa e publique:

```powershell
docker compose build
docker compose push
```

Aplique novamente os manifestos:

```powershell
kubectl apply -f .\k8s\configmap.yaml `
  --kubeconfig=$KUBECONFIG

kubectl apply -f .\k8s\auth.yaml `
  --kubeconfig=$KUBECONFIG

kubectl apply -f .\k8s\data-transform.yaml `
  --kubeconfig=$KUBECONFIG

kubectl apply -f .\k8s\patient-data.yaml `
  --kubeconfig=$KUBECONFIG

kubectl apply -f .\k8s\gateway.yaml `
  --kubeconfig=$KUBECONFIG

kubectl apply -f .\k8s\frontend.yaml `
  --kubeconfig=$KUBECONFIG

kubectl apply -f .\k8s\ingress.yaml `
  --kubeconfig=$KUBECONFIG
```

Evite reutilizar a mesma tag durante os experimentos. Tags distintas ajudam a identificar e reproduzir cada versão avaliada.

## 18. Endereços da aplicação

### Execução local com Docker Compose

```text
Frontend: http://localhost:3000/grupo2/
Gateway: http://localhost:5000
Métricas do Data Transform: http://localhost:8000/metrics
```

### Execução no Kubernetes

```text
Aplicação: https://kiriland.unb.br/grupo2/
```
