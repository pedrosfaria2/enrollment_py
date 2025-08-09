from __future__ import annotations

import json
from typing import Any

import pika
import pytest

from infra.messaging.rabbitmq import RabbitPublisher


class FakeChannel:
    def __init__(self, *, raise_on_publish: Exception | None = None, return_on_publish: bool = False):
        self.is_open = True
        self.declared = False
        self.declare_args: dict[str, Any] | None = None
        self.confirm_delivery_called = False
        self.return_cb = None
        self.basic_publish_calls: list[dict[str, Any]] = []
        self.raise_on_publish = raise_on_publish
        self.return_on_publish = return_on_publish

    def queue_declare(self, *, queue: str, durable: bool, auto_delete: bool):
        self.declared = True
        self.declare_args = {"queue": queue, "durable": durable, "auto_delete": auto_delete}

    def confirm_delivery(self):
        self.confirm_delivery_called = True

    def add_on_return_callback(self, cb):
        self.return_cb = cb

    def basic_publish(self, *, exchange: str, routing_key: str, body: bytes, properties, mandatory: bool):
        self.basic_publish_calls.append(
            {
                "exchange": exchange,
                "routing_key": routing_key,
                "body": body,
                "properties": properties,
                "mandatory": mandatory,
            }
        )
        if self.raise_on_publish:
            raise self.raise_on_publish
        if self.return_on_publish and mandatory and self.return_cb:
            self.return_cb(None, None, None, body)


class FakeConnection:
    instances: list[FakeConnection] = []

    def __init__(self, channel: FakeChannel):
        self._channel = channel
        self.is_open = True
        self.closed = False
        FakeConnection.instances.append(self)

    def channel(self):
        return self._channel

    def close(self):
        self.closed = True
        self.is_open = False


@pytest.fixture(autouse=True)
def patch_pika(monkeypatch):
    monkeypatch.setattr(pika, "URLParameters", lambda url: url)
    yield


def make_blocking_connection_factory(fake_ch: FakeChannel):
    def _factory(_params):
        return FakeConnection(fake_ch)

    return _factory


def test_bootstrap_declares_queue_and_confirms(monkeypatch):
    ch = FakeChannel()
    monkeypatch.setattr(pika, "BlockingConnection", make_blocking_connection_factory(ch))

    pub = RabbitPublisher(url="amqp://guest:guest@host/%2F", queue="enrollments.requests")
    pub.publish({"x": 1})

    assert ch.declared is True
    assert ch.declare_args == {"queue": "enrollments.requests", "durable": True, "auto_delete": False}
    assert ch.confirm_delivery_called is True
    assert ch.return_cb is not None

    assert len(ch.basic_publish_calls) == 1
    call = ch.basic_publish_calls[0]
    assert call["exchange"] == ""
    assert call["routing_key"] == "enrollments.requests"
    assert call["mandatory"] is True

    assert json.loads(call["body"].decode("utf-8")) == {"x": 1}
    props = call["properties"]
    assert props.content_type == "application/json"
    assert props.delivery_mode == 2


def test_reuses_open_channel(monkeypatch):
    ch = FakeChannel()
    monkeypatch.setattr(pika, "BlockingConnection", make_blocking_connection_factory(ch))

    FakeConnection.instances.clear()
    pub = RabbitPublisher(url="amqp://guest:guest@host/%2F", queue="q")
    pub.publish({"a": 1})
    pub.publish({"b": 2})

    assert len(FakeConnection.instances) == 1
    assert len(ch.basic_publish_calls) == 2


def test_unroutable_message_raises_and_resets(monkeypatch):
    ch = FakeChannel(return_on_publish=True)
    monkeypatch.setattr(pika, "BlockingConnection", make_blocking_connection_factory(ch))

    FakeConnection.instances.clear()
    pub = RabbitPublisher(url="amqp://guest:guest@host/%2F", queue="q")

    with pytest.raises(RuntimeError, match="message was returned"):
        pub.publish({"no_route": True})

    assert pub._conn is None  # type: ignore[attr-defined]
    assert pub._ch is None  # type: ignore[attr-defined]
    assert any(conn.closed for conn in FakeConnection.instances)


def test_publish_exception_resets_and_wraps(monkeypatch):
    ch = FakeChannel(raise_on_publish=RuntimeError("boom"))
    monkeypatch.setattr(pika, "BlockingConnection", make_blocking_connection_factory(ch))

    pub = RabbitPublisher(url="amqp://guest:guest@host/%2F", queue="q")
    with pytest.raises(RuntimeError, match="publish failed:"):
        pub.publish({"x": 1})

    assert pub._conn is None  # type: ignore[attr-defined]
    assert pub._ch is None  # type: ignore[attr-defined]


def test_reconnects_if_channel_closed(monkeypatch):
    ch1 = FakeChannel()
    ch2 = FakeChannel()
    first = FakeConnection(ch1)
    second = FakeConnection(ch2)

    created = []

    def factory(_params):
        if not created:
            created.append(first)
            return first
        created.append(second)
        return second

    monkeypatch.setattr(pika, "BlockingConnection", factory)

    pub = RabbitPublisher(url="amqp://guest:guest@host/%2F", queue="q")
    pub.publish({"one": 1})

    first.is_open = False
    ch1.is_open = False

    pub.publish({"two": 2})

    assert len(ch1.basic_publish_calls) == 1
    assert len(ch2.basic_publish_calls) == 1


def test_close_closes_connection(monkeypatch):
    ch = FakeChannel()
    fake_conn = FakeConnection(ch)
    monkeypatch.setattr(pika, "BlockingConnection", lambda _p: fake_conn)

    pub = RabbitPublisher(url="amqp://guest:guest@host/%2F", queue="q")
    pub.publish({"x": 1})
    pub.close()

    assert fake_conn.closed is True
    assert pub._conn is None  # type: ignore[attr-defined]
    assert pub._ch is None  # type: ignore[attr-defined]
