#!/usr/bin/env sh
set -eu
python -m grpc_tools.protoc -I../proto --python_out=. --grpc_python_out=. ../proto/transform.proto
echo "Arquivos gRPC gerados com sucesso."
