@echo off
python -m grpc_tools.protoc -I..\proto --python_out=. --grpc_python_out=. ..\proto\transform.proto
if errorlevel 1 exit /b %errorlevel%
echo Arquivos gRPC gerados com sucesso.
