from worker.main import build_message_handler


class DummyRedis:
    def __init__(self) -> None:
        self.store = {}

    def set(self, key: str, value: str) -> None:
        self.store[key] = value


class DummyChannel:
    def __init__(self) -> None:
        self.acked = False

    def basic_ack(self, delivery_tag: str) -> None:
        self.acked = True


class DummyMethod:
    delivery_tag = "tag-1"


def test_handler_sets_alert_and_acks() -> None:
    redis_client = DummyRedis()
    channel = DummyChannel()

    handler = build_message_handler(redis_client)
    handler(channel, DummyMethod(), None, b"disk-usage-high")

    assert redis_client.store["last_alert"] == "disk-usage-high"
    assert channel.acked is True
