import os
import time

import pika
import redis


def build_message_handler(redis_client: redis.Redis):
    def _handle_message(ch, method, properties, body: bytes) -> None:  # noqa: ANN001
        redis_client.set("last_alert", body.decode("utf-8"))
        ch.basic_ack(delivery_tag=method.delivery_tag)

    return _handle_message


def run() -> None:
    queue_name = os.getenv("QUEUE_NAME", "alerts")
    rabbitmq_host = os.getenv("RABBITMQ_HOST", "rabbitmq")
    redis_host = os.getenv("REDIS_HOST", "redis")

    while True:
        try:
            redis_client = redis.Redis(host=redis_host, port=6379, decode_responses=True)
            params = pika.ConnectionParameters(host=rabbitmq_host)
            connection = pika.BlockingConnection(params)
            channel = connection.channel()
            channel.queue_declare(queue=queue_name, durable=True)
            channel.basic_qos(prefetch_count=1)
            channel.basic_consume(
    queue=queue_name,
    on_message_callback=build_message_handler(redis_client),
)
            channel.start_consuming()
        except Exception:
            time.sleep(3)


if __name__ == "__main__":
    run()
