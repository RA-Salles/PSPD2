"""Servidor gRPC do microsserviço Data Transform."""

import json
import logging
import os
from concurrent import futures

import grpc
from prometheus_client import Counter, Histogram, start_http_server

import transform_pb2
import transform_pb2_grpc
from transformer import TransformError, transform_payload


REQUESTS = Counter("data_transform_grpc_requests_total", "Chamadas gRPC", ["method", "status", "access_level"])
LATENCY = Histogram("data_transform_grpc_duration_seconds", "Duração da transformação", ["method", "access_level"])


class DataTransformService(transform_pb2_grpc.DataTransformServiceServicer):
    def __init__(self, pseudonym_secret: str):
        self.pseudonym_secret = pseudonym_secret

    def TransformToFHIR(self, request, context):
        level = str(request.access_level or "").upper()
        with LATENCY.labels("TransformToFHIR", level or "MISSING").time():
            try:
                raw = json.loads(request.raw_database_json)
                result = transform_payload(raw, level, self.pseudonym_secret)
                encoded = json.dumps(result, ensure_ascii=False, separators=(",", ":"))
                REQUESTS.labels("TransformToFHIR", "OK", level).inc()
                return transform_pb2.TransformResponse(fhir_json_payload=encoded)
            except (json.JSONDecodeError, TransformError) as exc:
                REQUESTS.labels("TransformToFHIR", "INVALID_ARGUMENT", level or "MISSING").inc()
                context.abort(grpc.StatusCode.INVALID_ARGUMENT, str(exc))
            except Exception:
                logging.exception("Falha inesperada durante a transformação")
                REQUESTS.labels("TransformToFHIR", "INTERNAL", level or "MISSING").inc()
                context.abort(grpc.StatusCode.INTERNAL, "Falha interna no Data Transform")


def serve() -> None:
    logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"))
    port = int(os.getenv("GRPC_PORT", "50053"))
    metrics_port = int(os.getenv("METRICS_PORT", "8000"))
    secret = os.getenv("PSEUDONYM_SECRET", "dev-only-change-me")
    if secret == "dev-only-change-me":
        logging.warning("PSEUDONYM_SECRET não definido; usando segredo apenas para desenvolvimento")

    start_http_server(metrics_port)
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=int(os.getenv("GRPC_WORKERS", "10"))))
    transform_pb2_grpc.add_DataTransformServiceServicer_to_server(DataTransformService(secret), server)
    server.add_insecure_port(f"[::]:{port}")
    server.start()
    logging.info("Data Transform gRPC em :%s; métricas Prometheus em :%s/metrics", port, metrics_port)
    server.wait_for_termination()


if __name__ == "__main__":
    serve()
