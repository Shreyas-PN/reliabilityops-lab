import json
import os
import random
import time
from typing import Any

import pika
import redis


def _get_attempt(properties: pika.BasicProperties | None) -> int:
    if not properties or not properties.headers:
        return 0
    try:
        return int(properties.headers.get("x-attempt", 0))
    except Exception:
        return 0


def _publish(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    queue: str,
    body: bytes,
    attempt: int,
) -> None:
    channel.queue_declare(queue=queue, durable=True)
    channel.basic_publish(
        exchange="",
        routing_key=queue,
        body=body,
        properties=pika.BasicProperties(
            content_type="application/json",
            delivery_mode=2,
            headers={"x-attempt": attempt},
        ),
    )


def build_message_handler(
    channel: pika.adapters.blocking_connection.BlockingChannel,
    redis_client: redis.Redis,
    queue_name: str,
    dlq_name: str,
    max_retries: int,
    fail_rate: float,
):
    def _handle_message(ch, method, properties, body: bytes) -> None:  # noqa: ANN001
        attempt = _get_attempt(properties)

        try:
            msg: dict[str, Any] = json.loads(body.decode("utf-8"))
            task_id = str(msg.get("task_id", ""))
            payload = msg.get("payload", {}) or {}

            # Idempotency / last state (simple)
            status_key = f"task:{task_id}:status"

            # Simulate failure conditions
            should_fail = bool(payload.get("fail", False))
            if not should_fail and fail_rate > 0:
                should_fail = random.random() < fail_rate

            if should_fail:
                raise RuntimeError("Simulated failure")

            # "Process" task
            redis_client.set(status_key, "processed")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return

        except Exception as e:
            # Retry / DLQ path
            if attempt < max_retries:
                backoff = min(2 ** attempt, 10)
                time.sleep(backoff)

                # Re-publish with incremented attempt
                _publish(channel, queue_name, body, attempt + 1)
                redis_client.set(f"task:{task_id}:status", f"retrying:{attempt + 1}")
            else:
                # DLQ
                dlq_body = json.dumps(
                    {
                        "error": str(e),
                        "attempts": attempt,
                        "original": body.decode("utf-8", errors="replace"),
                    }
                ).encode("utf-8")
                _publish(channel, dlq_name, dlq_body, attempt)
                redis_client.set(f"task:{task_id}:status", "dlq")

            ch.basic_ack(delivery_tag=method.delivery_tag)

    return _handle_message


def run() -> None:
    queue_name = os.getenv("QUEUE_NAME", "tasks")
    dlq_name = os.getenv("DLQ_NAME", "tasks.dlq")
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    redis_host = os.getenv("REDIS_HOST", "redis")

    max_retries = int(os.getenv("MAX_RETRIES", "3"))
    fail_rate = float(os.getenv("FAIL_RATE", "0.0"))

    while True:
        try:
            redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)

            params = pika.ConnectionParameters(host=rabbitmq_host)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()

            channel.queue_declare(queue=queue_name, durable=True)
            channel.queue_declare(queue=dlq_name, durable=True)
            channel.basic_qos(prefetch_count=1)

            channel.basic_consume(
                queue=queue_name,
                on_message_callback=build_message_handler(
                    channel=channel,
                    redis_client=redis_client,
                    queue_name=queue_name,
                    dlq_name=dlq_name,
                    max_retries=max_retries,
                    fail_rate=fail_rate,
                ),
            )

            channel.start_consuming()
        except Exception:
            time.sleep(3)


if __name__ == "__main__":
    run()