import json


class DummyRedis:
    def __init__(self) -> None:
        self.store: dict[str, str] = {}

    def set(self, key: str, value: str) -> None:
        self.store[key] = value

    def get(self, key: str) -> str | None:
        return self.store.get(key)


class DummyChannel:
    def __init__(self) -> None:
        self.acked: list[int] = []
        self.published: list[tuple[str, bytes, dict]] = []
        self.declared: list[str] = []

    def basic_ack(self, delivery_tag: int) -> None:
        self.acked.append(delivery_tag)

    def queue_declare(self, queue: str, durable: bool = True) -> None:  # noqa: ARG002
        self.declared.append(queue)

    def basic_publish(self, exchange: str, routing_key: str, body: bytes, properties=None) -> None:  # noqa: ANN001, ARG002
        headers = {}
        if properties is not None and getattr(properties, "headers", None):
            headers = dict(properties.headers)
        self.published.append((routing_key, body, headers))


class DummyMethod:
    def __init__(self, delivery_tag: int) -> None:
        self.delivery_tag = delivery_tag


class DummyProperties:
    def __init__(self, headers: dict | None = None) -> None:
        self.headers = headers or {}


def test_handler_sets_processed_and_acks() -> None:
    from worker.main import build_message_handler

    redis_client = DummyRedis()
    channel = DummyChannel()

    handler = build_message_handler(
        channel=channel,
        redis_client=redis_client,  # type: ignore[arg-type]
        queue_name="tasks",
        dlq_name="tasks.dlq",
        max_retries=3,
        fail_rate=0.0,
    )

    body = json.dumps({"task_id": "t-1", "payload": {"hello": "world"}}).encode("utf-8")
    method = DummyMethod(delivery_tag=123)
    props = DummyProperties(headers={"x-attempt": 0})

    handler(channel, method, props, body)

    assert redis_client.get("task:t-1:status") == "processed"
    assert channel.acked == [123]
    assert channel.published == []


def test_handler_retries_then_dlq_and_acks() -> None:
    from worker.main import build_message_handler

    redis_client = DummyRedis()
    channel = DummyChannel()

    handler = build_message_handler(
        channel=channel,
        redis_client=redis_client,  # type: ignore[arg-type]
        queue_name="tasks",
        dlq_name="tasks.dlq",
        max_retries=0,  # immediate DLQ on first failure
        fail_rate=0.0,
    )

    body = json.dumps({"task_id": "t-2", "payload": {"fail": True}}).encode("utf-8")
    method = DummyMethod(delivery_tag=456)
    props = DummyProperties(headers={"x-attempt": 0})

    handler(channel, method, props, body)

    assert redis_client.get("task:t-2:status") == "dlq"
    assert channel.acked == [456]

    # Should publish exactly one message to DLQ
    assert len(channel.published) == 1
    routing_key, published_body, headers = channel.published[0]
    assert routing_key == "tasks.dlq"
    assert isinstance(published_body, (bytes, bytearray))
    assert isinstance(headers, dict)