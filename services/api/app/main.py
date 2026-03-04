from fastapi import FastAPI, HTTPException, Request
from pydantic import BaseModel

from starlette.responses import Response

import json
import os
import time
from typing import Any

import pika
import psycopg
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

app = FastAPI(title="reliabilityops-api")

# Prometheus metrics
HTTP_REQUESTS_TOTAL = Counter(
    "api_http_requests_total",
    "Total HTTP requests",
    ["method", "path", "status"],
)
HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "api_http_request_duration_seconds",
    "HTTP request duration in seconds",
    ["method", "path"],
)


class TaskIn(BaseModel):
    task_id: str
    payload: dict[str, Any]


@app.middleware("http")
async def metrics_middleware(request: Request, call_next):
    start = time.perf_counter()
    status_code = 500
    try:
        response = await call_next(request)
        status_code = response.status_code
        return response
    finally:
        duration = time.perf_counter() - start
        path = request.url.path
        HTTP_REQUESTS_TOTAL.labels(request.method, path, str(status_code)).inc()
        HTTP_REQUEST_DURATION_SECONDS.labels(request.method, path).observe(duration)


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok", "service": "api"}


@app.get("/")
def root() -> dict[str, str]:
    return {"message": "reliabilityops api"}


@app.get("/readyz")
def readyz() -> dict[str, Any]:
    db_dsn = os.getenv("DB_DSN")
    rabbit_url = os.getenv("RABBITMQ_URL")

    if not db_dsn or not rabbit_url:
        raise HTTPException(
            status_code=500,
            detail="Missing DB_DSN or RABBITMQ_URL environment variables",
        )

    # Check Postgres connectivity
    try:
        with psycopg.connect(db_dsn, connect_timeout=2) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1;")
                cur.fetchone()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Postgres not ready: {e}")

    # Check RabbitMQ connectivity
    try:
        params = pika.URLParameters(rabbit_url)
        params.socket_timeout = 2
        conn = pika.BlockingConnection(params)
        conn.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"RabbitMQ not ready: {e}")

    return {"status": "ok", "dependencies": {"postgres": "ok", "rabbitmq": "ok"}}


@app.post("/task")
def create_task(task: TaskIn) -> dict[str, Any]:
    rabbit_url = os.getenv("RABBITMQ_URL")
    queue_name = os.getenv("TASK_QUEUE", "tasks")

    if not rabbit_url:
        raise HTTPException(status_code=500, detail="Missing RABBITMQ_URL")

    message = {"task_id": task.task_id, "payload": task.payload}
    body = json.dumps(message).encode("utf-8")

    try:
        params = pika.URLParameters(rabbit_url)
        params.socket_timeout = 5
        connection = pika.BlockingConnection(params)
        channel = connection.channel()
        channel.queue_declare(queue=queue_name, durable=True)

        channel.basic_publish(
            exchange="",
            routing_key=queue_name,
            body=body,
            properties=pika.BasicProperties(
                content_type="application/json",
                delivery_mode=2,  # persistent
                headers={"x-attempt": 0},
            ),
        )
        connection.close()
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Failed to publish task: {e}")

    return {"status": "accepted", "queue": queue_name, "task_id": task.task_id}


@app.get("/metrics")
def metrics() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)